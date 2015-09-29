from trac.db.schema import Table, Column, Index
from datetime import datetime
from trac.util.datefmt import to_utimestamp, utc

class DisclaimerModel(object):
    disclaimer_schema = [
                      Table('disclaimer', key='id')[
                        Column('id', type='int', auto_increment=True),
                        Column('name'),
                        Column('version', type='int'),
                        Column('body'),
                        Column('author'),
                        Column('created', type='int64'),
                        Index(['name', 'version'])],
                      Table('user_disclaimer', key='id')[
                        Column('id', type='int', auto_increment=True),
                        Column('user'),
                        Column('disclaimer_name'),
                        Column('version', type='int'),
                        Column('body')]
                    ]  

    def __init__(self, env):
        self.env = env

    def _get_db(self, db=None):
        return db or self.env.get_read_db()
    
    def validate(self, name=None):
        max_version = 0
        count = 0
        db = self._get_db()
        cursor = db.cursor()
        if name:
            cursor.execute("""SELECT count(*), max(version) FROM disclaimer WHERE name=%s""", (name,))
            (count, max_version) = cursor.fetchone()
        if not max_version:
            max_version = 0
        return (count, max_version)
    
    def get_by_id(self, id):
        db = self._get_db()
        cursor = db.cursor()
        cursor.execute("""SELECT name, version FROM disclaimer WHERE id=%s""", (id,))
        return cursor.fetchone()
        
    def get_by_name(self, name):
        db = self._get_db()
        cursor = db.cursor()
        cursor.execute("""SELECT id, version, author, body FROM disclaimer WHERE name=%s""", (name,))
        return list(cursor)
    
    def get_by_name_version(self, name, version=None):
        db = self._get_db()
        cursor = db.cursor()
        if not version:
            count, version = self.validate(name)
        cursor.execute("""SELECT id, author, body FROM disclaimer WHERE name=%s and version=%s""", (name, version))
        return cursor.fetchone()
     
    def getall(self):
        data = {}
        db = self._get_db()
        cursor = db.cursor()
        cursor.execute("""SELECT * FROM disclaimer ORDER BY name, created""")
        for (id, name, version, body, author, created) in cursor:
            if name not in data:
                data[name] = [(id, version, body, author, created)]
            else:
                data[name].append((id, version, body, author, created))
        return data

    def insert(self, name, body, author, db=None):
        count, max_version = self.validate(name)
        created = to_utimestamp(datetime.now(utc))
        @self.env.with_transaction(db)
        def do_insert(db):
            cursor = db.cursor()
            cursor.execute("""INSERT INTO disclaimer (name,version,body,author,created) VALUES(%s,%s,%s,%s,%s)""",\
                                 (name, max_version+1, body, author, created))


    def update(self, new=None, old=None, db=None):
        @self.env.with_transaction(db)
        def do_update(db):
            cursor = db.cursor()
            if new and old:
                cursor.execute("""UPDATE disclaimer SET name=%s WHERE name=%s""", (new, old))
    
    def delete(self, id=None, db=None):
        @self.env.with_transaction(db)
        def do_delete(db):
            cursor = db.cursor()
            cursor.execute("DELETE FROM disclaimer WHERE id=%s", (id,))

class UserDisclaimerModel(object):
    def __init__(self, env):
        self.env = env

    def _get_db(self, db=None):
        return db or self.env.get_read_db()
    
    def insert(self, user, name, version, body, db=None):
        @self.env.with_transaction(db)
        def do_insert(db):
            cursor = db.cursor()
            cursor.execute("""INSERT INTO user_disclaimer (user, disclaimer_name, version, body) VALUES(%s,%s,%s,%s)""",\
                                 (user, name, version, body))
    
    def validate(self, user, name, version):
        db = self._get_db()
        cursor = db.cursor()
        cursor.execute("""SELECT count(*) FROM user_disclaimer WHERE user=%s and disclaimer_name=%s and version=%s""", (user, name, version))
        (count,) = cursor.fetchone()
        return count


