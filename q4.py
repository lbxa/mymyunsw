#!/usr/bin/python3
# Lucas Barbosa (z5259433)

import sys
import re
from helpers import GRADE_LOOKUP_FOR_UOC, GRADE_LOOKUP_FOR_WAM, Db, getStudent


class Transcript(Db):
    """Glorified stdouter

    Summary:
      The idea is to encapsulate all relevant information about how a requirement
      should be printed to stdout in this class so one can simply call
        t = Transcript(*args)
        print(t)
      and not worry about any logic leaking out.

    Args:
        Db (_type_): inherits from the Db class to query the database
    """

    def __init__(self, zid):
        super().__init__()
        self.zid = zid
        self.marks = getStudentMarks(self.conn, zid)
        self.grades_for_uoc = GRADE_LOOKUP_FOR_UOC
        self.grades_for_wam = GRADE_LOOKUP_FOR_WAM

    def is_grade_applicable(self, grade, target="wam") -> bool:
        return (
            self.grades_for_wam.get(grade, False)
            if target == "wam"
            else self.grades_for_uoc.get(grade, False)
        )

    def calc_uoc(self):
        applicable_uoc = [
            mark[-1]
            for mark in self.marks
            if self.is_grade_applicable(mark[4], target="uoc")
        ]

        return sum(applicable_uoc)

    def calc_wam(self):
        applicable_grades = [
            mark[3]
            for mark in self.marks
            if self.is_grade_applicable(mark[4], target="wam")
        ]
        if len(applicable_grades) == 0:
            return 0.0

        return sum(applicable_grades) / float(len(applicable_grades))

    def __format_mark(self, mark, grade, uoc):
        mark_result = str(uoc) + "uoc"

        if grade in ("AF", "FL", "UF", "E", "F"):
            mark_result = "fail"
        elif grade in (
            "AS",
            "AW",
            "PW",
            "NA",
            "RD",
            "NF",
            "NC",
            "LE",
            "PE",
            "WD",
            "WJ",
        ):
            mark_result = "unrs"

        return f"{mark if mark is not None else '-':>3} {grade:>2s}  {mark_result:2s}"

    def __format_marks(self):
        format_str = (
            lambda course_code, term, course_title, mark, grade, uoc: f"{course_code} {term} {course_title[:31]:<32s}{self.__format_mark(mark, grade, uoc)}"
        )
        return "\n".join(format_str(*mark) for mark in self.marks)

    def __format_uoc(self):
        return f"UOC = {self.calc_uoc()}"

    def __format_wam(self):
        return f"WAM = {self.calc_wam():.1f}"

    def __str__(self):
        return "\n".join(
            [self.__format_marks(), f"{self.__format_uoc()}, {self.__format_wam()}"]
        )

    def __del__(self):
        super().__del__()


### set up some globals

usage = f"Usage: {sys.argv[0]} zID"
db = None

### process command-line args

argc = len(sys.argv)
if argc < 2:
    print(usage)
    exit(1)
zid = sys.argv[1]
if zid[0] == "z":
    zid = zid[1:8]
digits = re.compile("^\d{7}$")
if not digits.match(zid):
    print(f"Invalid student ID {zid}")
    exit(1)


def getStudentEnrolment(db, zid) -> (str, str, str):
    cur = db.cursor()
    cur.execute(
        """
    select
      p.code,
      s.code,
      p.name,
      max(t.starting) as start_date
    from program_enrolments pe
    join stream_enrolments se on pe.id = se.part_of
    join streams s on se.stream = s.id
    join programs p on pe.program = p.id
    join people pep on pe.student = pep.id
    join terms t on pe.term = t.id
    where pep.zid = %s 
    group by 
      p.code,
      s.code,
      p.name
  """,
        (zid,),
    )
    info = cur.fetchone()
    cur.close()
    if not info:
        return None
    else:
        prog_code, stream_code, prog_name, _ = info
        return prog_code, stream_code, prog_name


def getStudentMarks(db, zid) -> (str, str, str, int, str, int):
    cur = db.cursor()
    cur.execute(
        """
    select
      s.code,
      t.code,
      s.title,
      ce.mark, 
      ce.grade,
      s.uoc
    from course_enrolments ce
    join courses c on ce.course = c.id
    join subjects s on c.subject = s.id
    join terms t on c.term = t.id
    join people p on ce.student = p.id
    where p.zid = %s
  """,
        (zid,),
    )
    info = cur.fetchall()
    cur.close()
    if not info:
        return []
    else:
        return info


try:
    db = Db()
    stuInfo = getStudent(db.conn, zid)
    if not stuInfo:
        print(f"Invalid student ID {zid}")
        exit()

    _, zid, family_name, given_names, full_name, origin = stuInfo
    print(f"{zid} {family_name}, {given_names}")

    prog_code, stream_code, prog_name = getStudentEnrolment(db.conn, zid)
    print(prog_code, stream_code, prog_name)

    t = Transcript(zid)
    print(t)

except Exception as err:
    print("DB error: ", err)
finally:
    if db:
        db.__del__()
