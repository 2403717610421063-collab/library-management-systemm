import os
import sqlite3
from flaskext.mysql import MySQL
from pymysql.cursors import DictCursor


class SQLiteDictCursor:
	def __init__(self, conn):
		self.conn = conn
		self.cursor = conn.cursor()

	def execute(self, q):
		self.cursor.execute(q)
		return self

	def fetchall(self):
		rows = self.cursor.fetchall()
		if not rows:
			return []
		cols = [description[0] for description in self.cursor.description]
		return [dict(zip(cols, row)) for row in rows]

	def fetchone(self):
		row = self.cursor.fetchone()
		if not row:
			return None
		cols = [description[0] for description in self.cursor.description]
		return dict(zip(cols, row))


class DB(object):
	"""Initialize database with MySQL or SQLite fallback"""
	host = os.environ.get("MYSQL_DATABASE_HOST", "localhost")
	user = os.environ.get("MYSQL_DATABASE_USER", "root")
	password = os.environ.get("MYSQL_DATABASE_PASSWORD", "")
	db = os.environ.get("MYSQL_DATABASE_DB", "lms")
	port = int(os.environ.get("MYSQL_DATABASE_PORT", 3306))
	table = ""

	def __init__(self, app):
		self.use_sqlite = False
		self.sqlite_conn = None

		# Only try MySQL if explicitly requested or if MYSQL_DATABASE_HOST is set in environment
		try_mysql = "MYSQL_DATABASE_HOST" in os.environ or os.environ.get("USE_MYSQL") == "true"

		if try_mysql:
			try:
				app.config["MYSQL_DATABASE_HOST"] = self.host
				app.config["MYSQL_DATABASE_USER"] = self.user
				app.config["MYSQL_DATABASE_PASSWORD"] = self.password
				app.config["MYSQL_DATABASE_DB"] = self.db
				app.config["MYSQL_DATABASE_PORT"] = self.port
				self.mysql = MySQL(app, cursorclass=DictCursor)
				with app.app_context():
					conn = self.mysql.connect()
					conn.close()
			except Exception as e:
				print("MySQL connection failed, using SQLite fallback:", e)
				self.use_sqlite = True
		else:
			self.use_sqlite = True

		if self.use_sqlite:
			db_path = "/tmp/lms.db" if os.path.exists("/tmp") else "lms.db"
			self.sqlite_conn = sqlite3.connect(db_path, check_same_thread=False)
			self.sqlite_conn.create_function("concat", 2, lambda a, b: str(a or '') + str(b or ''))
			self.init_sqlite_db()

	def init_sqlite_db(self):
		cursor = self.sqlite_conn.cursor()
		cursor.execute("CREATE TABLE IF NOT EXISTS admin (id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT, password TEXT)")
		cursor.execute("CREATE TABLE IF NOT EXISTS books (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, desc TEXT, author TEXT, availability INTEGER, edition TEXT, count INTEGER)")
		cursor.execute("CREATE TABLE IF NOT EXISTS reserve (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, book_id INTEGER)")
		cursor.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, email TEXT, password TEXT, bio TEXT, mob TEXT, lock INTEGER, created_at DATETIME DEFAULT CURRENT_TIMESTAMP)")

		cursor.execute("SELECT count(*) FROM books")
		if cursor.fetchone()[0] == 0:
			cursor.execute("INSERT INTO admin (id, email, password) VALUES (1, 'hamza@gmail.com', '025db420560617303c2ba988d050ec62562343bc0fb0358d31d2f0bae8dbede8')")
			cursor.execute("INSERT INTO books (id, name, desc, author, availability, edition, count) VALUES (1, '101 Ways To Be A Software Engineer', 'Lorem ipsum dolor sit amet, consectetur adipisicing elit.', 'Mr. Johnny Test', 1, '1', 3)")
			cursor.execute("INSERT INTO books (id, name, desc, author, availability, edition, count) VALUES (2, 'JAVA For Absolute Beginners', 'Step into the basics of java programming along with globally famed programmer', 'Author JAVA', 1, '1', 5)")
			cursor.execute("INSERT INTO users (id, name, email, password, bio, mob, lock) VALUES (1, 'Hamza', 'hamza@gmail.com', '025db420560617303c2ba988d050ec62562343bc0fb0358d31d2f0bae8dbede8', 'Book enthusiast.', '', 0)")
			cursor.execute("INSERT INTO reserve (id, user_id, book_id) VALUES (1, 1, 1)")
			self.sqlite_conn.commit()

	def cur(self):
		if self.use_sqlite:
			return SQLiteDictCursor(self.sqlite_conn)
		return self.mysql.get_db().cursor()

	def query(self, q):
		if len(self.table) > 0:
			q = q.replace("@table", self.table)

		if self.use_sqlite:
			cursor = SQLiteDictCursor(self.sqlite_conn)
			cursor.execute(q)
			return cursor

		h = self.cur()
		h.execute(q)
		return h

	def commit(self):
		if self.use_sqlite:
			self.sqlite_conn.commit()
		else:
			self.query("COMMIT;")