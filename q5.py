#!/usr/bin/python3
# COMP3311 21T3 Ass2 ... progression check for a given student

import sys
import psycopg2
import re
from helpers import SUBJECT_MASK, CourseMark, Requirement, Transcript, getRequirements, getStudent, getProgram, getStream, getStudentEnrolment, getStudentMarks

def redact_code(code: str, mask: int):
  return code[:mask] + '#' * (len(SUBJECT_MASK) - mask)

# define any local helper functions here
class ProgressionCheck(Transcript):
  def __init__(self, db, zid, prog_code, strm_code):
    super().__init__(db, zid)
    self.prog_code = prog_code
    self.strm_code = strm_code
    self.marks = [CourseMark(*mark, False) for mark in getStudentMarks(self.conn, zid)]
    self.uoc_requirement = None 
    self.missing_requirements = {}
    self.init_requirements()
  
  def get_uncounted_marks(self):
    return [mark for mark in self.marks if mark.req_name is False]
  
  def get_counted_uoc(self): 
    return [mark.uoc for mark in self.marks if mark.req_name is not False]
  
  def check_uoc_overflow(self, mark: CourseMark, requirement: Requirement):
    already_counted_uoc = [m.uoc for m in self.marks if m.req_name == requirement.name]

    if requirement.max_req == 0:
      return sum(already_counted_uoc) + mark.uoc <= requirement.min_req
    elif requirement.min_req == 0:
      return sum(already_counted_uoc) + mark.uoc <= requirement.max_req
    elif requirement.min_req == requirement.max_req:
      return sum(already_counted_uoc) + mark.uoc <= requirement.min_req

  """
  Strategy (stream first (stream first) (stream first) (stream first) (stream first) (stream first) (stream first) (stream first) (stream first)):
    1. core 
    2. elective 
    3. gened
    4. free
  """
  def init_requirements(self):
    strm_reqs = [Requirement(self.conn, *r) for r in getRequirements(self.conn, self.strm_code, "streams")]
    prog_reqs = [Requirement(self.conn, *r) for r in getRequirements(self.conn, self.prog_code, "programs")]

    # streams always go first
    reqs = strm_reqs + prog_reqs

    uoc_req = [req.min_req for req in prog_reqs if req.type == 'uoc'][0]
    self.uoc_requirement = uoc_req

    reqs_by_type = {
      'core': [r for r in reqs if r.type == 'core'],
      'elective': [r for r in reqs if r.type == 'elective'],
      'gened': [r for r in reqs if r.type == 'gened'],
      'free': [r for r in reqs if r.type == 'free'],
    }

    reqs_tracker = {
      'core': [],
      'elective': [],
      'gened': [],
      'free': [],
    }

    for req in reqs_by_type['core']:
      # print(req, req.code)
      for mark in self.get_uncounted_marks():
        if mark.course_code in req.acadobjs and mark.passed():
          mark.req_name = req.name
          # reqs_tracker['core'].append((req, mark.uoc))

    for req in reqs_by_type['elective']:
      # print(req, req.code)
      # prioritise courses with the same stream code
      for mark in self.get_uncounted_marks():
        if mark.course_code in req.acadobjs and mark.passed() and self.check_uoc_overflow(mark, req):
          mark.req_name = req.name 
          reqs_tracker['elective'].append(req)
      # then san for general patterns e.g. COMP4####
      for mark in self.get_uncounted_marks():
        if redact_code(mark.course_code, 5) in req.acadobjs and mark.passed() and self.check_uoc_overflow(mark, req):
          mark.req_name = req.name 
          reqs_tracker['elective'].append(req)

    for req in reqs_by_type['gened']:
      # print(req, req.code)
      # first prioritise GEN##### courses
      for mark in self.get_uncounted_marks():
        if redact_code(mark.course_code, 3) == 'GEN#####' and mark.passed() and self.check_uoc_overflow(mark, req):
          mark.req_name = req.name 
          reqs_tracker['gened'].append(req)
      # then scan the rest 
      for mark in self.get_uncounted_marks():
        if mark.passed() and self.check_uoc_overflow(mark, req):
          mark.req_name = req.name 
          reqs_tracker['gened'].append(req)

    for req in reqs_by_type['free']:
      # print(req, req.code)
      for mark in self.get_uncounted_marks() :
        if mark.passed() and self.check_uoc_overflow(mark, req):
          mark.req_name = req.name 
          reqs_tracker['free'].append(req)

    self.missing_requirements = reqs_tracker
      
    # for mark in self.get_uncounted_marks():
    #   print(mark)

    # print("=="*15)

    
  def format_missing_requirements(self):
    for req_type, missing_reqs in self.missing_requirements.items():
      for r in missing_reqs:
        pass

    return ""

  def format_progession_status(self):
    return "Eligible to graduate" if sum(self.get_counted_uoc()) >= self.uoc_requirement else self.format_missing_requirements()

  def calc_uoc(self):
      applicable_uoc = [
          mark.uoc
          for mark in self.marks
          if self.is_grade_applicable(mark.grade, target="uoc") and mark.req_name is not False
      ]

      return sum(applicable_uoc)

  def format_uoc(self):
        return f"UOC = {self.calc_uoc()}"

  def __str__(self):
      return "\n".join(
          [super().format_marks(), f"{self.format_uoc()}, {super().format_wam()}", self.format_progession_status()]
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
  db = psycopg2.connect("dbname=ass2")

  stu_info = getStudent(db, zid)
  if not stu_info:
    print(f"Invalid student id {zid}")
    exit(1)

  _, zid, family_name, given_names, _, _= stu_info 

  if not prog_code or not strm_code:
    prog_code, strm_code, _ = getStudentEnrolment(db, zid)

  if prog_code:
    prog_info = getProgram(db, prog_code)
    if not prog_info:
      print(f"Invalid program code {prog_code}")
      exit(1)

  _, _, prog_name = prog_info 

  if strm_code:
    strm_info = getStream(db, strm_code)
    if not strm_info:
      print(f"Invalid program code {strm_code}")
      exit(1)

  print(f"{zid} {family_name}, {given_names}")
  print(prog_code, strm_code, prog_name)

  pc = ProgressionCheck(db, zid, prog_code, strm_code)
  print(pc)

except Exception as err:
  print("DB error: ", err)
finally:
  if db:
    db.close()
