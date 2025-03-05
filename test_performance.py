import os
import sqlite3
from datetime import datetime
import time
import threading
from contextlib import contextmanager
import logging
from typing import List, Dict, Optional, Any, Set
import unittest
import random
import string
from memory_manager import BiographicalMemory

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class TreeNode:
    def __init__(self, byte_value):
        self.byte = byte_value
        self.children = [None] * 8

    def set_child(self, index, value):
        if 0 <= index < 8:
            self.children[index] = value

class BiographicalMemory:
    OPTIMIZATION_PRAGMAS = [
        "PRAGMA journal_mode=WAL",
        "PRAGMA synchronous=NORMAL",
        "PRAGMA cache_size=10000",
        "PRAGMA temp_store=MEMORY",
        "PRAGMA mmap_size=30000000000"
    ]

    def __init__(self, db_path):
        """Initialize the biographical memory with the given database path."""
        self.db_path = db_path
        self.connections = {}
        self._initialize_db()
        self.metrics = {'store': [], 'retrieve': [], 'batch': []}

    def _initialize_db(self):
        """Initialize database with size optimizations."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            # Apply optimizations
            for pragma in self.OPTIMIZATION_PRAGMAS:
                cursor.execute(pragma)

            # Create table with consistent schema
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS biographies (
                    name TEXT NOT NULL UNIQUE,
                    birth_year INTEGER,
                    birth_place TEXT,
                    death_year INTEGER,
                    death_place TEXT,
                    occupation TEXT,
                    achievement TEXT,
                    education TEXT,
                    nationality TEXT,
                    known_for TEXT
                )
            """)
            
            # Create index for faster name lookups
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_name ON biographies(name)")
            
            conn.commit()
            logger.debug("Database initialized with size optimizations")
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise

    def verify_database(self):
        """Verify that the database and table exist."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sqlite_master WHERE type='table' AND name='biographies'")
        return cursor

    def get_connection(self):
        """Get or create a database connection for the current thread."""
        thread_id = threading.get_ident()
        if thread_id not in self.connections:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            self.connections[thread_id] = conn
            logger.debug(f"Created optimized connection in thread {thread_id}")
        return self.connections[thread_id]

    def store(self, name, data):
        """Store biographical data."""
        if not name or not isinstance(name, str):
            raise ValueError("Name must be a non-empty string")

        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO biographies
                (name, birth_year, birth_place, death_year, death_place,
                occupation, achievement, education, nationality, known_for)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                name,
                data.get('birth_year'),
                data.get('birth_place'),
                data.get('death_year'),
                data.get('death_place'),
                data.get('occupation'),
                data.get('achievement'),
                data.get('education'),
                data.get('nationality'),
                data.get('known_for')
            ))
            conn.commit()
        except sqlite3.IntegrityError as e:
            logger.error(f"Store failed due to integrity error: {e}")
            raise
        except Exception as e:
            logger.error(f"Store failed: {e}")
            raise

    def retrieve(self, name, field):
        """Retrieve a specific field for a person."""
        start_time = time.time()
        valid_columns = {
            'name', 'birth_year', 'birth_place', 'death_year', 'death_place',
            'occupation', 'achievement', 'education', 'nationality', 'known_for'
        }
        
        if field not in valid_columns:
            logger.error(f"Retrieve failed: Invalid field: {field}")
            return None

        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT {field} FROM biographies WHERE name = ?
            """, (name,))
            result = cursor.fetchone()
            value = result[0] if result else None
            duration = time.time() - start_time
            rate = 1 / duration if duration > 0 else 0
            self.metrics['retrieve'].append(rate)
            return value
        except Exception as e:
            logger.error(f"Retrieve failed: {e}")
            return None

    def batch_store(self, records: List[Dict[str, Any]], batch_size: int = 1000) -> List[int]:
        """High-performance batch storage with input validation.
        
        Args:
            records (List[Dict[str, Any]]): List of records to store
            batch_size (int, optional): Number of records per batch. Defaults to 1000.
            
        Returns:
            List[int]: List of inserted record IDs
        """
        if not records:
            return []
            
        # Validate all records before processing
        for r in records:
            if 'name' not in r or not isinstance(r['name'], str) or not r['name'].strip():
                raise ValueError("Each record must have a non-empty 'name' string")
        
        start_time = time.time()
        inserted_ids = []
        
        conn = self.get_connection()
        try:
            with conn:
                cursor = conn.cursor()
                for i in range(0, len(records), batch_size):
                    batch = records[i:i + batch_size]
                    values = [
                        (
                            r['name'],
                            r.get('birth_year'),
                            r.get('birth_place'),
                            r.get('death_year'),
                            r.get('death_place'),
                            r.get('occupation'),
                            r.get('achievement'),
                            r.get('education'),
                            r.get('nationality'),
                            r.get('known_for')
                        )
                        for r in batch
                    ]
                    cursor.executemany(
                        """INSERT INTO biographies 
                        (name, birth_year, birth_place, death_year, death_place,
                        occupation, achievement, education, nationality, known_for) 
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        values
                    )
                    # Retrieve inserted IDs based on unique names
                    names = [r['name'] for r in batch]
                    cursor.execute(f"SELECT rowid FROM biographies WHERE name IN ({','.join(['?']*len(names))})", names)
                    ids = [row[0] for row in cursor.fetchall()]
                    inserted_ids.extend(ids)
                
                duration = time.time() - start_time
                rate = len(records) / duration
                self.metrics['batch'].append(rate)
                logger.debug(f"Batch store rate: {rate:.2f} records/second")
                return inserted_ids
        except sqlite3.IntegrityError as e:
            logger.error(f"Batch store failed due to integrity error: {e}")
            raise
        except Exception as e:
            logger.error(f"Batch store failed: {e}")
            raise

    def build_tree(self, data: Dict[str, Any]) -> TreeNode:
        """Build a tree from biographical data."""
        root = TreeNode("11100000")
        personal = TreeNode("11100000")
        personal.set_child(0, data.get('name', ''))
        personal.set_child(1, data.get('birth_year', ''))
        personal.set_child(2, data.get('birth_place', ''))
        personal.set_child(3, data.get('death_year', ''))
        personal.set_child(4, data.get('death_place', ''))
        personal.set_child(5, data.get('occupation', ''))
        personal.set_child(6, data.get('achievement', ''))
        personal.set_child(7, data.get('education', ''))
        root.set_child(0, personal)
        return root

    def __del__(self):
        """Close all database connections when the object is destroyed."""
        self.close()

    def close(self):
        """Close all database connections."""
        logger.debug("Closing BiographicalMemory")
        # Only close the connection for the current thread
        thread_id = threading.get_ident()
        if thread_id in self.connections:
            self.connections[thread_id].close()
            del self.connections[thread_id]
            logger.debug(f"Closed connection for thread {thread_id}")

    def get_performance_metrics(self):
        """Return average performance metrics."""
        return {
            'batch_store_rate': sum(self.metrics['batch']) / len(self.metrics['batch']) if self.metrics['batch'] else 0,
            'retrieve_rate': sum(self.metrics['retrieve']) / len(self.metrics['retrieve']) if self.metrics['retrieve'] else 0
        }

def generate_random_person():
    """Generate random biographical data."""
    return {
        'name': ''.join(random.choices(string.ascii_letters, k=10)),
        'birth_year': random.randint(1700, 2000),
        'birth_place': ''.join(random.choices(string.ascii_letters, k=8)),
        'death_year': random.randint(1750, 2023),
        'death_place': ''.join(random.choices(string.ascii_letters, k=8)),
        'occupation': ''.join(random.choices(string.ascii_letters, k=12)),
        'achievement': ''.join(random.choices(string.ascii_letters, k=20)),
        'nationality': ''.join(random.choices(string.ascii_letters, k=8)),
        'known_for': ''.join(random.choices(string.ascii_letters, k=20))
    }

class TestDatabasePerformance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up class-level resources."""
        cls.test_db = "test_performance.db"
        if os.path.exists(cls.test_db):
            os.remove(cls.test_db)
        cls.memory = BiographicalMemory(cls.test_db)
        logger.debug("Test class setup complete")

    @classmethod
    def tearDownClass(cls):
        """Clean up class-level resources."""
        if hasattr(cls, 'memory'):
            # Close only the main thread's connection
            thread_id = threading.get_ident()
            if thread_id in cls.memory.connections:
                cls.memory.connections[thread_id].close()
                del cls.memory.connections[thread_id]
            
            # Clear the connections dict
            cls.memory.connections.clear()
            
        if os.path.exists(cls.test_db):
            try:
                os.remove(cls.test_db)
            except PermissionError:
                time.sleep(0.2)
                try:
                    os.remove(cls.test_db)
                except:
                    pass
        logger.debug("Test class teardown complete")

    def test_insertion_performance(self):
        """Test performance of inserting records."""
        print("\nTesting insertion performance:")
        batch_sizes = [10, 100]
        
        for size in batch_sizes:
            # Generate and store test data
            records = [generate_random_person() for _ in range(size)]
            
            # Test individual inserts
            start_time = time.time()
            for record in records:
                self.memory.store(record['name'], record)
            duration = time.time() - start_time
            rate = size / duration
            print(f"Individual inserts: {size} records in {duration:.2f} seconds")
            print(f"Rate: {rate:.2f} records/second")
            
            # Test batch insert
            records = [generate_random_person() for _ in range(size)]
            start_time = time.time()
            self.memory.batch_store(records)
            duration = time.time() - start_time
            rate = size / duration
            print(f"Batch insert: {size} records in {duration:.2f} seconds")
            print(f"Rate: {rate:.2f} records/second")

    def test_retrieval_performance(self):
        """Test performance of retrieving records."""
        print("\nTesting retrieval performance:")
        test_data = generate_random_person()
        self.memory.store(test_data['name'], test_data)
        
        start_time = time.time()
        for _ in range(100):
            self.memory.retrieve(test_data['name'], 'birth_year')
        duration = time.time() - start_time
        rate = 100 / duration
        print(f"Retrieved 100 times in {duration:.2f} seconds")
        print(f"Rate: {rate:.2f} retrievals/second")

    def test_concurrent_performance(self):
        """Test concurrent operations."""
        print("\nTesting concurrent performance:")
        num_threads = 5
        operations_per_thread = 100
        
        def worker():
            for _ in range(operations_per_thread):
                person = generate_random_person()
                try:
                    self.memory.store(person['name'], person)
                except Exception as e:
                    logger.error(f"Worker thread error: {e}")

        threads = [threading.Thread(target=worker) for _ in range(num_threads)]
        start_time = time.time()
        
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        duration = time.time() - start_time
        total_ops = num_threads * operations_per_thread
        print(f"Completed {total_ops} operations in {duration:.2f} seconds")
        print(f"Rate: {total_ops/duration:.2f} operations/second")

    def test_database_size(self):
        """Test database size growth."""
        print("\nTesting database size growth:")
        sizes = [100, 500]
        
        for size in sizes:
            records = [generate_random_person() for _ in range(size)]
            self.memory.batch_store(records)
            
            db_size = os.path.getsize(self.test_db) / 1024  # Size in KB
            print(f"Database with {size} records: {db_size:.2f} KB")
            print(f"Average size per record: {db_size/size:.2f} KB")

if __name__ == '__main__':
    unittest.main(verbosity=2)