import os
from tree_node import TreeNode
import sqlite3
from datetime import datetime
import time
from functools import lru_cache
import threading
from queue import Queue, Full, Empty
from contextlib import contextmanager
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class ConnectionPool:
    def __init__(self, db_path, max_connections=20):
        self.db_path = db_path
        self.max_connections = max_connections
        self._lock = threading.Lock()
        self._local = threading.local()
        logger.debug(f"Initialized ConnectionPool with {max_connections} max connections")

    def get_connection(self):
        if not hasattr(self._local, 'connection'):
            with self._lock:
                self._local.connection = sqlite3.connect(self.db_path, timeout=10)
                logger.debug(f"Created new connection in thread {threading.get_ident()}")
        return self._local.connection

    def close_all(self):
        if hasattr(self._local, 'connection'):
            try:
                self._local.connection.close()
                del self._local.connection
                logger.debug(f"Closed connection in thread {threading.get_ident()}")
            except Exception as e:
                logger.error(f"Error closing connection: {e}")

class BiographicalMemory:
    def __init__(self, db_path):
        """Initialize the biographical memory."""
        self.db_path = db_path
        self._lock = threading.Lock()
        self._pool = ConnectionPool(db_path)
        self._initialize_db()
        
        # Enable WAL mode for better concurrent performance
        with self._get_cursor() as cursor:
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.execute("PRAGMA cache_size=10000")
            cursor.execute("PRAGMA temp_store=MEMORY")

        self._add_indexes()
        self._cache = {}
        self._connection_cache = {}
        logger.debug("Initialized BiographicalMemory with db: %s", db_path)

    @contextmanager
    def _get_cursor(self):
        """Context manager for database cursor with automatic cleanup."""
        conn = self._pool.get_connection()
        cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cursor.close()
            self._pool.close_all()

    def _initialize_db(self):
        """Initialize the database schema."""
        logger.debug("Initializing database")
        conn = self._pool.get_connection()
        with conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS people (
                    id INTEGER PRIMARY KEY,
                    name TEXT,
                    age INTEGER,
                    occupation TEXT,
                    bio TEXT
                )
            ''')
            logger.debug("Database initialized")

    def _add_indexes(self):
        """Add indexes for frequently queried fields."""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            try:
                cursor = conn.cursor()
                
                # Index for name searches
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_people_name ON people(name)")
                
                # Index for birth year queries
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_birth_year ON people(age)")
                
                # Index for nationality searches
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_nationality ON people(occupation)")
                
                conn.commit()
            finally:
                conn.close()

    def get_connection(self):
        return self._pool.get_connection()

    def build_tree(self, data):
        """Build a tree from biographical data.
        
        Args:
            data (dict): Dictionary containing biographical data
            
        Returns:
            TreeNode: Root node of the constructed tree
        """
        root = TreeNode("11100000")  # Root byte
        
        # Personal info (Bit 0)
        personal = TreeNode("11100000")
        personal.set_child(0, data.get('name', ''))        # Name
        personal.set_child(1, data.get('age', ''))  # Birth year
        personal.set_child(2, data.get('occupation', ''))  # Occupation
        
        # Set root's first child to personal info
        root.set_child(0, personal)
        
        return root

    def store(self, name, data):
        """Store a single biographical record."""
        logger.debug("Storing data for %s", name)
        if not name or not isinstance(data, dict):
            return False

        conn = self.get_connection()
        with conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO people (name, age, occupation, bio) VALUES (?, ?, ?, ?)",
                (name, data.get('age'), data.get('occupation'), data.get('bio'))
            )
            last_id = cursor.lastrowid
            logger.debug("Stored data with ID %s", last_id)
            return last_id

    def retrieve(self, person_id):
        logger.debug("Retrieving person with ID %s", person_id)
        conn = self.get_connection()
        with conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM people WHERE id = ?", (person_id,))
            result = cursor.fetchone()
            if result:
                return {
                    'id': result[0],
                    'name': result[1],
                    'age': result[2],
                    'occupation': result[3],
                    'bio': result[4]
                }
        return None
    
    def get_all_people(self):
        """Get a list of all people in the database."""
        with self._get_cursor() as cursor:
            cursor.execute("SELECT name FROM people")
            return [row[0] for row in cursor.fetchall()]

    def batch_store(self, records):
        """Store multiple biographical records efficiently."""
        if not records or not isinstance(records, list):
            return False

        with self._lock, self._get_cursor() as cursor:
            try:
                cursor.executemany('''
                    INSERT OR REPLACE INTO people 
                    (name, age, occupation, bio)
                    VALUES (:name, :age, :occupation, :bio)
                ''', records)
                return True
            except sqlite3.Error:
                return False

    def bulk_retrieve(self, names):
        """Retrieve multiple records efficiently."""
        if not names:
            return []

        placeholders = ', '.join(['?' for _ in names])
        with self._get_cursor() as cursor:
            cursor.execute(f"SELECT * FROM people WHERE name IN ({placeholders})", names)
            results = cursor.fetchall()
            
            return [
                dict(zip(['name', 'age', 'occupation', 'bio'], row))
                for row in results
            ]

    def close(self):
        """Close all database connections."""
        logger.debug("Closing BiographicalMemory")
        self._pool.close_all()

    def __del__(self):
        """Ensure connections are closed on object deletion."""
        try:
            self.close()
        except:
            pass 