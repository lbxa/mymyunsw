#!/usr/bin/python3
# Lucas Barbosa (z5259433)

import sys
import psycopg2
import re
from helpers import  Transcript, getRequirements, getStudent, getStudentEnrolment

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

try:
    db = psycopg2.connect("dbname=a2 user=a2 password=password host=localhost")
    stuInfo = getStudent(db, zid)
    if not stuInfo:
        print(f"Invalid student ID {zid}")
        exit()

    _, zid, family_name, given_names, full_name, origin = stuInfo
    print(f"{zid} {family_name}, {given_names}")

    prog_code, stream_code, prog_name = getStudentEnrolment(db, zid)
    print(prog_code, stream_code, prog_name)

    t = Transcript(db, zid)
    print(t)

except Exception as err:
    print("DB error: ", err)
finally:
    if db:
         db.close()
