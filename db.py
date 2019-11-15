"""
 Implements a simple database of users.

"""

import sqlite3
conn = sqlite3.connect('database.db', check_same_thread=False)


def dict_factory(cursor, row):
    """Converts table row to dictionary."""
    res = {}
    for idx, col in enumerate(cursor.description):
        res[col[0]] = row[idx]
    return res


conn.row_factory = dict_factory


def create_db():
    """Recreates the database."""
    c = conn.cursor()
    c.execute("DROP TABLE IF EXISTS user")
    c.execute("DROP TABLE IF EXISTS cache")
    c.execute("""
        CREATE TABLE user (
            address TEXT,
            username TEXT,
            password TEXT,
            user_logged_in INTEGER
        )
        """)
    c.execute("""
        CREATE TABLE cache (
            url TEXT,
            requests INTEGER
        )
        """)
    conn.commit()


''' ------------------- Table User -------------------- '''


def get_users():
    """Returns all users."""
    res = conn.cursor().execute('SELECT * FROM user')
    return res.fetchall()


def get_user(username, password):
    """Returns a single user."""
    res = conn.cursor().execute("SELECT * FROM user WHERE username = '%s' AND password = '%s'" % (username, password))
    return res.fetchone()


def add_user(address, username, password):
    """Adds a new user."""
    stmt = "INSERT INTO user VALUES ('%s', '%s', '%s', '%s')" % (address, username, password, 0)
    c = conn.cursor()
    c.execute(stmt)
    conn.commit()
    return get_user(c.lastrowid, c.lastrowid)


def get_user_login(username, password):
    """Returns a user data for login."""
    res = conn.cursor().execute("SELECT address FROM user WHERE username = '%s' AND password = '%s'" % (username, password))
    return res.fetchone()


def update_user(username, password, address):
    """Updates a user data."""
    stmt = "UPDATE user SET username='%s', password='%s' WHERE address= '%s'" % (username, password, address)
    conn.cursor().execute(stmt)
    conn.commit()
    return get_user(username, password)


def get_user_status(address):
    """Returns the status of a user"""
    res = conn.cursor().execute("SELECT user_logged_in FROM user WHERE address = '%s'" % address)
    return res.fetchone()


def get_user_logged_in_credentials(address):
    """Returns the status of uses logged in."""
    res = conn.cursor().execute("SELECT username, password FROM user WHERE address = '%s' " % address)
    return res.fetchone()


def update_user_logged_in_status(status, address, username, password):
    """Updates a user with the given data."""
    stmt = "UPDATE user SET user_logged_in = '%s' " \
           "WHERE address = '%s' and username='%s' and password='%s'" % (status, address, username, password)
    conn.cursor().execute(stmt)
    conn.commit()
    return get_user_status(address)


def delete_user(address, username, password):
    """Deletes a user."""
    stmt = "DELETE FROM user WHERE address='%s' AND username='%s' AND password='%s'" % (address, username, password)
    conn.cursor().execute(stmt)
    conn.commit()


''' ------------------- Table cache -------------------- '''


def get_url_in_cache(request_filename):
    """Returns a url in cache."""
    res = conn.cursor().execute("SELECT url FROM cache WHERE url = '%s'" % request_filename)
    return res.fetchone()


def save_file(request_filename):
    """Adds a new url to cache"""
    stmt = "INSERT INTO cache VALUES ('%s', '%s')" % (request_filename, 1)
    c = conn.cursor()
    c.execute(stmt)
    conn.commit()
    return get_user(c.lastrowid, c.lastrowid)


def get_requests_url(request_filename):
    """Returns number of requests specific url."""
    res = conn.cursor().execute("SELECT requests FROM cache WHERE url = '%s'" % request_filename)
    return res.fetchone()


def set_requests_url(requests, request_filename):
    """Updates a user with the given data."""
    stmt = "UPDATE cache SET requests=%s WHERE url= '%s'" % (requests, request_filename)
    conn.cursor().execute(stmt)
    conn.commit()
    return get_requests_url(request_filename)


def get_top2_url(n):
    """Returns the 2 most visited url"""
    res = conn.cursor().execute("SELECT * FROM cache ORDER BY requests DESC LIMIT %s" % n)
    return res.fetchall()
