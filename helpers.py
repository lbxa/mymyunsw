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
