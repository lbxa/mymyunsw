# COMP3311 21T3 Ass2 ... Python helper functions
# add here any functions to share between Python scripts
# you must submit this even if you add nothing

import psycopg2

SUBJECT = "########"
STREAM = "######"
PROGRAM = "####"

GRADE_LOOKUP_FOR_UOC = {
    "PS": True,
    "CR": True,
    "DN": True,
    "HD": True,
    "XE": True,
    "T": True,
    "SY": True,
    "EC": True,
    "RC": True,
    "AF": False,
    "FL": False,
    "UF": False,
    "E": False,
    "F": False,
    "AS": False,
    "AW": False,
    "NA": False,
    "PW": False,
    "RD": False,
    "NF": False,
    "NC": False,
    "LE": False,
    "PE": False,
    "WD": False,
    "WJ": False,
}

GRADE_LOOKUP_FOR_WAM = {
    "PS": True,
    "CR": True,
    "DN": True,
    "HD": True,
    "XE": False,
    "T": False,
    "SY": False,
    "EC": False,
    "RC": False,
    "AF": True,
    "FL": True,
    "UF": True,
    "E": True,
    "F": True,
    "AS": False,
    "AW": False,
    "NA": False,
    "PW": False,
    "RD": False,
    "NF": False,
    "NC": False,
    "LE": False,
    "PE": False,
    "WD": False,
    "WJ": False,
}

class Db:
    """Connect to the database

    The only intention of this class is to connect to be inherited by other classes
    that wish to connect to the pg database instance

    TODO: Make this a singleton class
    """

    def __init__(self):
        self._db = psycopg2.connect("dbname=a2 user=a2 password=password host=localhost")

    @property
    def conn(self):
        return self._db

    @conn.setter
    def conn(self, value):
        self._db = value

    def __del__(self):
        self._db.close()

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
        applicable_marks = [
            (mark[3], mark[-1])
            for mark in self.marks
            if self.is_grade_applicable(mark[4], target="wam")
        ]

        total_attempted_uoc = [mark[-1] for mark in applicable_marks]

        if len(total_attempted_uoc) == 0:
            return 0.0

        weighted_mark = [mark * uoc for mark, uoc in applicable_marks]

        return sum(weighted_mark) / float(sum(total_attempted_uoc))

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

def getProgram(db, code):
    cur = db.cursor()
    cur.execute("select * from Programs where code = %s", [code])
    info = cur.fetchone()
    cur.close()
    if not info:
        return None
    else:
        return info


def getStream(db, code):
    cur = db.cursor()
    cur.execute("select name from Streams where code = %s", [code])
    info = cur.fetchone()
    cur.close()
    if not info:
        return None
    else:
        return info


def getStudent(db, zid):
    cur = db.cursor()
    qry = """
    select p.*
    from   People p
            join Students s on s.id = p.id
    where  p.zid = %s
    """
    cur.execute(qry, [zid])
    info = cur.fetchone()
    cur.close()
    if not info:
        return None
    else:
        return info

def getSubject(db, subject):
    cur = db.cursor()
    cur.execute("""
    select title 
    from subjects
    where code = %s
    """,
        (subject,),
    )
    (title,) = cur.fetchone()
    return title

def getStudentMarks(db, zid) -> (str, str, str, int, str, int):
    cur = db.cursor()
    cur.execute("""
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
        order by 
            t.starting asc, 
            s.code
    """, (zid,),)
    info = cur.fetchall()
    cur.close()
    if not info:
        return []
    else:
        return info
