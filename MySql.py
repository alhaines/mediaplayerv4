# MySql.py
#
# Copyright 2010 AL Haines (from original MyFunctions.php)
#
# This module provides a Pythonic class for interacting with a MySQL database,
# translating the functionality found in the original PHP MyFunctions.php.
# It adheres to modularity and securely retrieves database credentials from
# the user-provided 'config.py' file.

import pymysql
import pymysql.cursors
import sys

# Initialize credential variables as None
DB_HOST = None
DB_USER = None
DB_PASSWORD = None
DB_NAME = None

try:
    import config

    # Attempt to load from mysql_config dictionary first
    if hasattr(config, 'mysql_config') and isinstance(config.mysql_config, dict):
        # Use .get() with a default of None to avoid KeyError if a key is missing
        DB_HOST = config.mysql_config.get('host')
        DB_USER = config.mysql_config.get('user')
        DB_PASSWORD = config.mysql_config.get('password')
        DB_NAME = config.mysql_config.get('database')

    # If any credential is still None, try to load from individual variables as fallback
    if DB_HOST is None and hasattr(config, 'SERVER'):
        DB_HOST = config.SERVER
    if DB_USER is None and hasattr(config, 'USER'):
        DB_USER = config.USER
    if DB_PASSWORD is None and hasattr(config, 'PASSWORD'):
        DB_PASSWORD = config.PASSWORD
    if DB_NAME is None and hasattr(config, 'DATABASE'):
        DB_NAME = config.DATABASE

    # Final validation: Ensure all required credentials are set
    if not all([DB_HOST, DB_USER, DB_PASSWORD, DB_NAME]):
        print("Warning: Database credentials are not fully defined in config.py. Using fallbacks.", file=sys.stderr)

except ImportError:
    print("Error: config.py not found. Database credentials cannot be loaded.", file=sys.stderr)
    exit()

class MySQL:
    """
    A class for managing connections and queries to a MySQL database.
    """
    def __init__(self, host=None, user=None, password=None, database=None):
        """
        Initializes the MySQL class with database credentials.
        Prefers arguments, falls back to global config variables.
        """
        self.host = host or DB_HOST
        self.user = user or DB_USER
        self.password = password or DB_PASSWORD
        self.database = database or DB_NAME
        self.conn = None

        if not all([self.host, self.user, self.password, self.database]):
            print("Error: MySQL credentials are not fully configured.", file=sys.stderr)
            exit()

    def _connect(self):
        """
        Establishes a connection to the database.
        """
        if self.conn and self.conn.open:
            return self.conn
        try:
            self.conn = pymysql.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database,
                cursorclass=pymysql.cursors.DictCursor
            )
            return self.conn
        except pymysql.Error as e:
            print(f"Connection error: {e}", file=sys.stderr)
            return None

    def _close(self):
        """
        Closes the database connection.
        """
        if self.conn:
            self.conn.close()
            self.conn = None

    def get_data(self, query, params=None):
        """
        Executes a SELECT query and returns the results as a list of dictionaries.
        """
        conn = self._connect()
        if not conn:
            return []
        try:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                results = cursor.fetchall()
                return results
        except pymysql.Error as e:
            print(f"Query execution error: {e}", file=sys.stderr)
            return []
        finally:
            self._close()

    def put_data(self, query, params=None):
        """
        Executes an INSERT, UPDATE, or DELETE query and returns the number of
        affected rows.
        """
        conn = self._connect()
        if not conn:
            return 0
        try:
            with conn.cursor() as cursor:
                affected_rows = cursor.execute(query, params)
                conn.commit()
                return affected_rows
        except pymysql.Error as e:
            print(f"Query execution error: {e}", file=sys.stderr)
            conn.rollback()
            return 0
        finally:
            self._close()

    def get_field_names(self, table):
        """
        Retrieves the field (column) names for a given table.
        """
        field_names = []
        conn = None
        try:
            conn = self._connect()
            with conn.cursor() as cursor:
                cursor.execute(f"DESCRIBE `{table}`")
                columns = cursor.fetchall()
                field_names = [col['Field'] for col in columns]
        except pymysql.Error as e:
            print(f"Error getting field names for table '{table}': {e}", file=sys.stderr)
        finally:
            if conn:
                self._close()
        return field_names

    def get_num_fields(self, table):
        """
        Retrieves the number of fields (columns) in a given table.
        """
        num_fields = -1
        conn = None
        try:
            conn = self._connect()
            with conn.cursor() as cursor:
                cursor.execute(f"DESCRIBE `{table}`")
                num_fields = cursor.rowcount
        except pymysql.Error as e:
            print(f"Error getting number of fields for table '{table}': {e}", file=sys.stderr)
        finally:
            if conn:
                self._close()
        return num_fields

# Global helper functions (add_quotes_double, add_quotes_single)
# are now largely redundant due to parameterized queries, but kept for direct translation reference.

def add_quotes_double(text):
    """
    Adds double quotes around a string and escapes existing double/single quotes
    within the string for use in contexts like SQL.
    Note: For SQL queries, prefer parameterized queries over manual quoting.
    """
    text = str(text).replace('"', '`').replace("'", '%') # Ensure text is string
    return f'"{text}"'

def add_quotes_single(text):
    """
    Adds single quotes around a string and escapes existing double/single quotes
    within the string for use in contexts like SQL.
    Note: For SQL queries, prefer parameterized queries over manual quoting.
    """
    text = str(text).replace('"', '`').replace("'", '%') # Ensure text is string
    return f"'{text}'"

