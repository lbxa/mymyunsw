#!/usr/bin/python3
# COMP3311 21T3 Ass2 ... progression check for a given student

import sys
import re
from typing import override
from helpers import Db, Transcript, getStudent, getProgram, getStream, getStudentEnrolment

# define any local helper functions here
class ProgressionCheck(Transcript):
  def __init__(self, zid, prog_code, strm_code):
    super().__init__(zid)
    self.prog_code = prog_code
    self.strm_code = strm_code

  @override
  def __str__(self):
    return super().__str__()

  @override
  def __del__(self):
    return super().__del__()

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

prog_code = None
strm_code = None

if argc == 4:
  prog_code = sys.argv[2]
  strm_code = sys.argv[3]

# manipulate database

try:
  db = Db()

  stu_info = getStudent(db.conn,zid)
  if not stu_info:
    print(f"Invalid student id {zid}")
    exit(1)

  _, zid, family_name, given_names, full_name, origin =stu_info 

  if not prog_code or not strm_code:
    prog_code, strm_code, _ = getStudentEnrolment(db.conn, zid)

  if prog_code:
    progInfo = getProgram(db.conn, prog_code)
    if not progInfo:
      print(f"Invalid program code {prog_code}")
      exit(1)

  if strm_code:
    strmInfo = getStream(db.conn, strm_code)
    if not strmInfo:
      print(f"Invalid program code {strm_code}")
      exit(1)

    _, zid, family_name, given_names, full_name, origin = stu_info 
    print(f"Student: {zid} {full_name}")
    pc = ProgressionCheck(zid, prog_code, strm_code)
    print(pc)

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
