#!/usr/bin/python3
# Lucas Barbosa (z5259433)

import sys
import psycopg2
from psycopg2 import sql  
from helpers import getProgram, getStream, getSubject, SUBJECT

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

class Requirement(Db):
  """Glorified stdouter

  Summary:
    The idea is to encapsulate all relevant information about how a requirement
    should be printed to stdout in this class so one can simply call 
      r = Requirement(*args)
      print(r)
    and not worry about any logic leaking out.

  Args:
      Db (_type_): inherits from the Db class to query the database
  """
  def __init__(self, code, name, type, min_req, max_req, acadobjs: str) -> None:
    super().__init__()
    self.name = name
    self.code = code
    self.type = type
    self.min_req = min_req if min_req is not None else 0
    self.max_req = max_req if max_req is not None else 0
    self.acadobjs = acadobjs

  def __acadobj_desc(self, acadobj) -> str:
    if type(acadobj) is list:
      return [getSubject(self.conn, obj) for obj in acadobj]
            
    return getSubject(self.conn, acadobj) if len(acadobj) == len(SUBJECT) else getStream(self.conn, acadobj)[0]

  """ Does a lot of the heavy lifting
  
  Parse acadobjs into a list of subjects/streams and return strings in accordance
  to the logic specific in the Requirement spec
  """
  def __parse_acadobjs(self) -> list: 
      if self.acadobjs is not None:
        obj_list = [s.strip() for s in self.acadobjs.split(",")]
        for i, obj in enumerate(obj_list):
          if obj[0] == "{" and obj[-1] == "}":
            obj_list[i] = obj[1:-1].split(";")
        
        format = lambda s, dash = False: f"{'- ' if dash else ''}{s} {self.__acadobj_desc(s)}" 
        return '\n'.join('- ' + '\n  or '.join([format(sublist) for sublist in obj]) if type(obj) is list else format(obj, True) for obj in obj_list)

  """Help parse max/min criteria for UOC requirements
  
  If max == null => "at least min UOC"
  If min == null => "up to MAX UOC"
  If min == max => "min/max UOC"
  
  Note max == null and min == null CANNOT happen
  """
  def uoc_minmax(self):
    min_uoc, max_uoc = self.min_req, self.max_req
    action_lookup = {
      0: f"{min_uoc}", 
      1: f"at least {min_uoc}", 
      2: f"up to {max_uoc}", 
      3: f"between {min_uoc} and {max_uoc}"
    }

    p = 0
    if max_uoc == 0:
      p += 1
    elif min_uoc == 0:
      p += 2
    elif min_uoc != max_uoc:
      p += 3

    action = action_lookup.get(p, 0)
    
    return f"{action} UOC"
    
  def format_uoc_req(self):
    return f"{self.name} {self.uoc_minmax()}"

  def format_stream_req(self):
    return f"1 stream from {name}\n{self.__parse_acadobjs()}"

  def format_core_req(self):
    return f"all courses from {self.name}\n{self.__parse_acadobjs()}"
 
  def format_elective_req(self):
    return f"{self.uoc_minmax()} courses from {self.name}\n- {self.acadobjs}"
  
  def format_gened_req(self):
    return f"{self.uoc_minmax()} of General Education"
  
  def format_free_req(self):
    return f"{self.uoc_minmax()} of {self.name}" 

  """Lookup table for formatting all requirements types

  Everything goes through this here :D
  """
  def __str__(self) -> str:
    format_lookup = {
      'uoc': self.format_uoc_req,
      'stream': self.format_stream_req,
      'core': self.format_core_req,
      'elective': self.format_elective_req,
      'gened': self.format_gened_req,
      "free": self.format_free_req
    }
    
    format = format_lookup.get(self.type, "Invalid requirement type")
    return format()

def getRequirements(db, code, table="streams"):
  if table not in ("programs", "streams"):
    raise ValueError("table should be 'programs' or 'streams'")
        
  fields = [
    "j.code", # streams.code or programs.code
    "r.name",
    "r.rtype",
    "r.min_req",
    "r.max_req",
    "r.acadobjs"
  ]

  join_table = "streams" if table == "streams" else "programs"
  join_field = f"for_{join_table[:-1]}"
  
  query = sql.SQL("""
    select {fields} 
    from requirements r 
    join {join_table} j on r.{join_field} = j.id 
    where j.code = %s
    order by r.id
  """).format(
    fields=sql.SQL(', ').join(map(lambda f: sql.Identifier(*f.split(".")), fields)),
    join_table=sql.Identifier(join_table),
    join_field=sql.Identifier(join_field)
  )

  cur = db.cursor()
  cur.execute(query, (code,))
  return cur.fetchall()

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
    db.__del__()
