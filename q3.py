#!/usr/bin/python3
# Lucas Barbosa (z5259433)

import sys
from helpers import Db, Requirement, getProgram, getRequirements, getStream  

### set up some globals

usage = f"Usage: {sys.argv[0]} (ProgramCode|StreamCode)"
db = None

### process command-line args

argc = len(sys.argv)
if argc < 2:
    print(usage)
    exit(1)
code = sys.argv[1]
if len(code) == 4:
    codeOf = "program"
elif len(code) == 6:
    codeOf = "stream"
else:
    print("Invalid code")
    exit(1)

try:
    db = Db()
    if codeOf == "program":
        progInfo = getProgram(db.conn, code)
        if not progInfo:
            print(f"Invalid program code {code}")
            exit(1)

        _, code, progName = progInfo
        print(code, progName)
        print("Academic Requirements:")

        for progReq in getRequirements(db.conn, code, table=codeOf + "s"):
            code, name, rtype, min_req, max_req, acadobjs = progReq
            r = Requirement(*progReq)
            print(r)

    elif codeOf == "stream":
        strmInfo = getStream(db.conn, code)
        if not strmInfo:
            print(f"Invalid stream code {code}")
            exit(1)

        print(code, strmInfo[0])
        print("Academic Requirements:")

        for streamReq in getRequirements(db.conn, code, table=codeOf + "s"):
            r = Requirement(*streamReq)
            print(r)


except Exception as err:
    print(err)
finally:
    if db:
         db.conn.close()
