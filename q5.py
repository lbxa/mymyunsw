#!/usr/bin/python3
# COMP3311 21T3 Ass2 ... progression check for a given student

import sys
import re
from helpers import CourseMark, Db, Requirement, Transcript, getRequirements, getStudent, getProgram, getStream, getStudentEnrolment, getStudentMarks

# define any local helper functions here
class ProgressionCheck(Transcript):
  def __init__(self, zid, prog_code, strm_code):
    super().__init__(zid)
    self.prog_code = prog_code
    self.strm_code = strm_code
    self.marks = [CourseMark(*mark, "req") for mark in getStudentMarks(self.conn, zid)]

  def __str__(self):
      return "\n".join(
          [super().format_marks(), f"{super().format_uoc()}, {super().format_wam()}"]
      )


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

try:
  db = Db()

  stu_info = getStudent(db.conn,zid)
  if not stu_info:
    print(f"Invalid student id {zid}")
    exit(1)

  _, zid, family_name, given_names, _, _= stu_info 

  if not prog_code or not strm_code:
    prog_code, strm_code, _ = getStudentEnrolment(db.conn, zid)

  if prog_code:
    prog_info = getProgram(db.conn, prog_code)
    if not prog_info:
      print(f"Invalid program code {prog_code}")
      exit(1)

  _, _, prog_name = prog_info 

  if strm_code:
    strm_info = getStream(db.conn, strm_code)
    if not strm_info:
      print(f"Invalid program code {strm_code}")
      exit(1)

  strm_name, = strm_info 
  print(strm_name)

  print(f"{zid} {family_name}, {given_names}")
  print(prog_code, strm_code, prog_name)

  pc = ProgressionCheck(zid, prog_code, strm_code)
  print(pc)

  strm_reqs = [Requirement(*r) for r in getRequirements(db.conn, strm_code, "streams")]
  prog_reqs = [Requirement(*r) for r in getRequirements(db.conn, prog_code, "programs")]

  """
  strategy
    1. core 
    2. elective 
    3. gened
    4. free
  """

  for prog_req in prog_reqs:
      print(prog_req)

  for strm_req in strm_reqs:
      print(strm_req)

  # if have a program/stream
  #   show progression check on supplied program/stream
  # else
  #   show progression check on most recent program/stream enrolment

  # ... add your code here ...

except Exception as err:
  print("DB error: ", err)
finally:
  if db:
    db.conn.close()
