#!/usr/bin/python3
# Lucas Barbosa (z5259433)

import psycopg2
from collections import defaultdict

# define any local helper functions here
# ...

### set up some globals

db = None

### process command-line args

try:
    db = psycopg2.connect("dbname=a2 user=a2 password=password host=localhost")

    cur = db.cursor()

    start, end = "19T1", "23T3"
    cur.execute(
        """
      select 
        pe.student, 
        s.status,
        t.code,
        p.name
      from program_enrolments pe
      join terms t on pe.term = t.id
      join programs p on pe.program = p.id
      join students s on pe.student = s.id
      where t.code between %s and %s
  """,
        (start, end),
    )

    students_by_term = defaultdict(list)
    stu_cache = set()

    for tup in cur.fetchall():
        zid, status, term, program = tup

        stu_hash = str(zid) + "#" + term
        if stu_hash in stu_cache:
            continue

        stu_cache.add(stu_hash)

        student = {
            "zid": zid,
            "term": term,
            "status": status if status == "INTL" else "LOCL",
            "program": program,
        }

        students_by_term[term].append(student)

    print("Term  #Locl  #Intl Proportion")
    for term, students in students_by_term.items():
        locl = len([student for student in students if student["status"] == "LOCL"])
        intl = len([student for student in students if student["status"] == "INTL"])
        prop = locl / float(intl)
        print(f"{term} {locl:6d} {intl:6d} {prop:6.1f}")

except Exception as err:
    print(err)
finally:
    if db:
        db.close()
