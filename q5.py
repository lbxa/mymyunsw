#!/usr/bin/python3
# COMP3311 21T3 Ass2 ... progression check for a given student

import sys
import psycopg2
import re
from helpers import Db, getStudent, getProgram, getStream
# from q4 import Transcript

# define any local helper functions here

### set up some globals

usage = f"Usage: {sys.argv[0]} zID [Program Stream]"
db = None

### process command-line args

argc = len(sys.argv)
if argc < 2:
  print(usage)
  exit(1)
zid = sys.argv[1]
if zid[0] == 'z':
  zid = zid[1:8]
digits = re.compile("^\d{7}$")
if not digits.match(zid):
  print("Invalid student ID")
  exit(1)

progCode = None
strmCode = None

if argc == 4:
  progCode = sys.argv[2]
  strmCode = sys.argv[3]

# manipulate database

try:
  db = Db()

  stuInfo = getStudent(db.conn,zid)
  if not stuInfo:
    print(f"Invalid student id {zid}")
    exit(1)
  #print(stuInfo) # debug

  if progCode:
    progInfo = getProgram(db.conn,progCode)
    if not progInfo:
      print(f"Invalid program code {progCode}")
      exit(1)
    #print(progInfo)  #debug

  if strmCode:
    strmInfo = getStream(db.conn,strmCode)
    if not strmInfo:
      print(f"Invalid program code {strmCode}")
      exit(1)
    #print(strmInfo)  #debug

    _, zid, family_name, given_names, full_name, origin = stuInfo
    print(f"Student: {zid} {full_name}")
    # t = Transcript(zid)
    # print(t)

  # if have a program/stream
  #   show progression check on supplied program/stream
  # else
  #   show progression check on most recent program/stream enrolment

  # ... add your code here ...

except Exception as err:
  print("DB error: ", err)
finally:
  if db:
    db.__del__()

