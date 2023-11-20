#!/usr/bin/python3
# Lucas Barbosa (z5259433)

import sys
import psycopg2
import re
from helpers import getSubject

NULL_CHAR = f"{'?':>6}"

"""
Sanitise an attribute to a string of length 6 for clean formatting
to stdout
"""
def sanitise(attr):
  if attr is None:
    return NULL_CHAR
  elif isinstance(attr, int):
    return f"{attr:6d}"
  else:
    return f"{attr:6s}"


usage = f"Usage: {sys.argv[0]} SubjectCode"
db = None

argc = len(sys.argv)
if argc < 2:
  print(usage)
  exit(1)
subject = sys.argv[1]
check = re.compile("^[A-Z]{4}[0-9]{4}$")
if not check.match(subject):
  print("Invalid subject code")
  exit(1)


try:
  db = psycopg2.connect("dbname=a2 user=a2 password=password host=localhost")
  subjectInfo = getSubject(db,subject)
  if not subjectInfo:
      print(f"Invalid subject code {subject}")
      exit(1)

  # List satisfaction for subject over time
  cur = db.cursor()
  start, end = '19T1', '23T3'
  cur.execute("""
      select
        t.code,
        c.satisfact,
        c.nresponses,
        count(ce.student) as students,
        p.full_name
      from courses c
      join subjects s on c.subject = s.id
      left join course_enrolments ce on c.id = ce.course
      join terms t on c.term = t.id
      join people p on c.convenor = p.id 
      where 
        t.code between %s and %s 
        and s.code = %s
      group by
        t.code,
        c.satisfact,
        c.nresponses,
        p.full_name
      order by t.code;
  """, (start, end, subject)) 

  print(f"{subject} {subjectInfo}")
  print("Term  Satis  #resp   #stu  Convenor")
  for tup in cur.fetchall():
    term, satisf, responses, students, convenor = tup
    print(f"{term} {sanitise(satisf)} {sanitise(responses)} {sanitise(students)}  {sanitise(convenor)}")


except Exception as err:
  print(err)
finally:
  if db:
    db.close()
