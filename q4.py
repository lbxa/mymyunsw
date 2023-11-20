#!/usr/bin/python3
# Lucas Barbosa (z5259433)

import sys
import re
from helpers import  Db, Transcript, getStudent

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
