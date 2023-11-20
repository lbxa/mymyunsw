# COMP3311 21T3 Ass2 ... Python helper functions
# add here any functions to share between Python scripts
# you must submit this even if you add nothing

import psycopg2
from psycopg2 import sql
import itertools

SUBJECT_MASK = "########"
STREAM_MASK = "######"
PROGRAM_MASK = "####"

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
        self.db = psycopg2.connect("dbname=a2 user=a2 password=password host=localhost")

    @property
    def conn(self):
        return self.db

    @conn.setter
    def conn(self, value):
        self.db = value

    # def __del__(self):
    #     self.db.close()

class Requirement(Db):
    """Glorified stdouter

    Summary:
      The idea is to encapsulate all relevant information about how a requirement
      should be printed to stdout in this class so one can simply call
        r = Requirement(*args)
        print(r)
      and not worry about any logic leaking out.

    Args:
        Db (_type_): inherits from the Db class to query the database
    """

    def __init__(self, code, name, type, min_req, max_req, acadobjs: str) -> None:
        super().__init__()
        self.name = name
        self.code = code
        self.type = type
        self.min_req = min_req if min_req is not None else 0
        self.max_req = max_req if max_req is not None else 0
        self.acadobjs = acadobjs

    def __acadobj_desc(self, acadobj) -> str:
        if type(acadobj) is list:
            return [getSubject(self.conn, obj) for obj in acadobj]

        return (
            getSubject(self.conn, acadobj)
            if len(acadobj) == len(SUBJECT_MASK)
            else getStream(self.conn, acadobj)[0]
        )

    """ Does a lot of the heavy lifting
  
    Parse acadobjs into a list of subjects/streams and return strings in accordance
    to the logic specific in the Requirement spec
    """
    def parse_acadobjs(self):
        obj_list = [s.strip() for s in self.acadobjs.split(",")]
        for i, obj in enumerate(obj_list):
            if obj[0] == "{" and obj[-1] == "}":
                obj_list[i] = obj[1:-1].split(";")
                
        return obj_list
     
    def __format_acadobjs(self) -> list:
        if self.acadobjs is not None:
            acadobjs_list = self.parse_acadobjs() 

            format = (
                lambda s, dash=False: f"{'- ' if dash else ''}{s} {self.__acadobj_desc(s)}"
            )
            return "\n".join(
                "- " + "\n  or ".join([format(sublist) for sublist in obj])
                if type(obj) is list else format(obj, True)
                for obj in acadobjs_list
            )

    """Help parse max/min criteria for UOC requirements
  
    If max == null => "at least min UOC"
    If min == null => "up to MAX UOC"
    If min == max => "min/max UOC"
    
    Note max == null and min == null CANNOT happen
    """

    def uoc_minmax(self):
        min_uoc, max_uoc = self.min_req, self.max_req
        action_lookup = {
            0: f"{min_uoc}",
            1: f"at least {min_uoc}",
            2: f"up to {max_uoc}",
            3: f"between {min_uoc} and {max_uoc}",
        }

        p = 0
        if max_uoc == 0:
            p += 1
        elif min_uoc == 0:
            p += 2
        elif min_uoc != max_uoc:
            p += 3

        action = action_lookup.get(p, 0)

        return f"{action} UOC"

    def format_uoc_req(self):
        return f"{self.name} {self.uoc_minmax()}"

    def format_stream_req(self):
        return f"1 stream from {self.name}\n{self.__format_acadobjs()}"

    def format_core_req(self):
        return f"all courses from {self.name}\n{self.__format_acadobjs()}"

    def format_elective_req(self):
        return f"{self.uoc_minmax()} courses from {self.name}\n- {self.acadobjs}"

    def format_gened_req(self):
        return f"{self.uoc_minmax()} of General Education"

    def format_free_req(self):
        return f"{self.uoc_minmax()} of {self.name}"

    """Lookup table for formatting all requirements types

    Everything goes through this here :D
    """
    def __str__(self) -> str:
        format_lookup = {
            "uoc": self.format_uoc_req,
            "stream": self.format_stream_req,
            "core": self.format_core_req,
            "elective": self.format_elective_req,
            "gened": self.format_gened_req,
            "free": self.format_free_req,
        }

        format = format_lookup.get(self.type, "Invalid requirement type")
        return format()

    # def __del__(self):
    #     super().__del__()

class CourseMark:
    def __init__(self, course_code, term, course_title, mark, grade, uoc, req_name): 
        self.course_code = course_code
        self.term = term
        self.course_title = course_title
        self.mark = mark
        self.grade = grade
        self.uoc = uoc
        self.req_name = req_name
    
    def sanitise_failing_grade(self):
        sanitised_grade = False
        if self.grade in ("AF", "FL", "UF", "E", "F"):
            sanitised_grade = "fail"
        elif self.grade in ("AS", "AW", "PW", "NA", "RD", "NF", "NC", "LE", "PE", "WD", "WJ"):
            sanitised_grade = "unrs"

        return sanitised_grade
    
    def passed(self):
       return self.sanitise_failing_grade() not in ('fail', 'unrs')
    
    def __format_grade(self):
        sanitised_grade = self.sanitise_failing_grade()
        mark_outcome = str(self.uoc if self.req_name is not False else 0) + "uoc" if not sanitised_grade else sanitised_grade
        mark = self.mark if self.mark is not None else '-'

        return f"{mark:>3} {self.grade:>2s}  {mark_outcome:2s}"

    def __format_req_name(self):
        if self.req_name is None:
            return ""
        elif self.req_name is False:
            if self.passed():
                return "  Could not be allocated"
            return ""
        else:
            return "  " + self.req_name 

    def __str__(self):
        return f"{self.course_code} {self.term} {self.course_title[:31]:<32s}{self.__format_grade()}{self.__format_req_name()}"

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
        self.marks = [CourseMark(*mark, None) for mark in getStudentMarks(self.conn, zid)]
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
            mark.uoc
            for mark in self.marks
            if self.is_grade_applicable(mark.grade, target="uoc")
        ]

        return sum(applicable_uoc)

    def calc_wam(self):
        applicable_marks = [
            (mark.mark, mark.uoc)
            for mark in self.marks
            if self.is_grade_applicable(mark.grade, target="wam")
        ]

        total_attempted_uoc = [uoc for _, uoc in applicable_marks]

        if len(total_attempted_uoc) == 0:
            return 0.0

        weighted_mark = [mark * uoc for mark, uoc in applicable_marks]

        return sum(weighted_mark) / float(sum(total_attempted_uoc))
    
    def sanitise_failing_grade(self, grade):
        sanitised_grade = False
        if grade in ("AF", "FL", "UF", "E", "F"):
            sanitised_grade = "fail"
        elif grade in ("AS", "AW", "PW", "NA", "RD", "NF", "NC", "LE", "PE", "WD", "WJ"):
            sanitised_grade = "unrs"

        return sanitised_grade

    def format_marks(self):
        return "\n".join(mark.__str__() for mark in self.marks)

    def format_uoc(self):
        return f"UOC = {self.calc_uoc()}"

    def format_wam(self):
        return f"WAM = {self.calc_wam():.1f}"

    def __str__(self):
        return "\n".join(
            [self.format_marks(), f"{self.format_uoc()}, {self.format_wam()}"]
        )

    # def __del__(self):
    #     super().__del__()

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
    cur.close()
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

def getStudentEnrolment(db, zid) -> (str, str, str):
    cur = db.cursor()
    cur.execute("""
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
    """, (zid,),)
    info = cur.fetchone()
    cur.close()
    if not info:
        return None
    else:
        prog_code, stream_code, prog_name, _ = info
        return prog_code, stream_code, prog_name

def getRequirements(db, code, table="streams"):
    if table not in ("programs", "streams"):
        raise ValueError("table should be 'programs' or 'streams'")

    fields = [
        "j.code",  # streams.code or programs.code
        "r.name",
        "r.rtype",
        "r.min_req",
        "r.max_req",
        "r.acadobjs",
    ]

    join_table = "streams" if table == "streams" else "programs"
    join_field = f"for_{join_table[:-1]}"

    query = sql.SQL("""
        select {fields} 
        from requirements r 
        join {join_table} j on r.{join_field} = j.id 
        where j.code = %s
        order by r.id
    """).format(
        fields=sql.SQL(", ").join(map(lambda f: sql.Identifier(*f.split(".")), fields)),
        join_table=sql.Identifier(join_table),
        join_field=sql.Identifier(join_field),
    )

    cur = db.cursor()
    cur.execute(query, (code,))
    requirements = cur.fetchall()
    cur.close()
    return requirements 