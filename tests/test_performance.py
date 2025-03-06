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
from functools import wraps

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

    @staticmethod
    def _generate_test_records(count):
        """Generate test records with consistent structure."""
        names = ["Alice", "Bob", "Charlie", "David", "Eve", "Frank", "Grace", "Henry", "Ivy", "Jack"]
        occupations = ["Engineer", "Doctor", "Artist", "Teacher", "Scientist", "Writer", "Chef", "Architect", "Musician", "Developer"]
        
        records = []
        for i in range(count):
            record = {
                'name': f"{random.choice(names)}_{i}",
                'birth_year': random.randint(1900, 2000),
                'occupation': random.choice(occupations)
            }
            records.append(record)
        
        return records

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

def test_category(*categories):
    """Decorator to assign categories to test methods"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        wrapper.test_categories = set(categories)
        return wrapper
    return decorator

class TestDatabasePerformance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up class-level resources."""
        cls.db_path = "test_performance.db"
        if os.path.exists(cls.db_path):
            os.remove(cls.db_path)
        cls.memory = BiographicalMemory(cls.db_path)
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
            
        if os.path.exists(cls.db_path):
            try:
                os.remove(cls.db_path)
            except PermissionError:
                time.sleep(0.2)
                try:
                    os.remove(cls.db_path)
                except:
                    pass
        logger.debug("Test class teardown complete")

    def setUp(self):
        # Create the table if it doesn't exist
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS biographical_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                birth_year INTEGER NOT NULL,
                occupation TEXT NOT NULL
            )
        """)
        conn.commit()
        cursor.close()
        conn.close()

    def generate_test_records(self, count):
        """Generate test records with consistent structure."""
        names = ["Alice", "Bob", "Charlie", "David", "Eve", "Frank", "Grace", "Henry", "Ivy", "Jack"]
        occupations = ["Engineer", "Doctor", "Artist", "Teacher", "Scientist", "Writer", "Chef", "Architect", "Musician", "Developer"]
        
        records = []
        for i in range(count):
            record = {
                'name': f"{random.choice(names)}_{i}",
                'birth_year': random.randint(1900, 2000),
                'occupation': random.choice(occupations)
            }
            records.append(record)
        
        return records

    @test_category('performance', 'benchmark')
    def test_insertion_performance(self):
        """Test performance of inserting records."""
        print("\nTesting insertion performance:")
        conn = None
        cursor = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Test small batch (10 records)
            records = self.generate_test_records(10)
            
            # Individual inserts
            start_time = time.time()
            for record in records:
                cursor.execute(
                    """INSERT INTO biographical_data 
                       (name, birth_year, occupation) 
                       VALUES (:name, :birth_year, :occupation)""",
                    record
                )
                conn.commit()
            duration = time.time() - start_time
            print(f"Individual inserts: 10 records in {duration:.2f} seconds")
            print(f"Rate: {10/duration:.2f} records/second")
            
            # Batch insert
            start_time = time.time()
            cursor.executemany(
                """INSERT INTO biographical_data 
                   (name, birth_year, occupation) 
                   VALUES (:name, :birth_year, :occupation)""",
                records
            )
            conn.commit()
            duration = time.time() - start_time
            print(f"Batch insert: 10 records in {duration:.2f} seconds")
            print(f"Rate: {10/duration:.2f} records/second")
            
            # Test larger batch (100 records)
            records = self.generate_test_records(100)
            
            # Individual inserts
            start_time = time.time()
            for record in records:
                cursor.execute(
                    """INSERT INTO biographical_data 
                       (name, birth_year, occupation) 
                       VALUES (:name, :birth_year, :occupation)""",
                    record
                )
                conn.commit()
            duration = time.time() - start_time
            print(f"Individual inserts: 100 records in {duration:.2f} seconds")
            print(f"Rate: {100/duration:.2f} records/second")
            
            # Batch insert
            start_time = time.time()
            cursor.executemany(
                """INSERT INTO biographical_data 
                   (name, birth_year, occupation) 
                   VALUES (:name, :birth_year, :occupation)""",
                records
            )
            conn.commit()
            duration = time.time() - start_time
            print(f"Batch insert: 100 records in {duration:.2f} seconds")
            print(f"Rate: {100/duration:.2f} records/second")
            
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    @test_category('performance', 'benchmark')
    def test_retrieval_performance(self):
        """Test performance of retrieving records."""
        print("\nTesting retrieval performance:")
        conn = None
        cursor = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Insert test data if needed
            records = self.generate_test_records(100)
            cursor.executemany(
                """INSERT INTO biographical_data 
                   (name, birth_year, occupation) 
                   VALUES (:name, :birth_year, :occupation)""",
                records
            )
            conn.commit()
            
            # Test retrieval performance
            start_time = time.time()
            for _ in range(100):
                cursor.execute("SELECT * FROM biographical_data ORDER BY RANDOM() LIMIT 1")
                cursor.fetchone()
            duration = time.time() - start_time
            
            print(f"Retrieved 100 times in {duration:.2f} seconds")
            print(f"Rate: {100/duration:.2f} retrievals/second")
            
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            raise
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    @test_category('performance', 'concurrent')
    def test_concurrent_performance(self):
        """Test concurrent operations."""
        print("\nTesting concurrent performance:")
        num_threads = 5
        operations_per_thread = 100
        lock = threading.Lock()
        connections = []
        
        def worker():
            conn = None
            cursor = None
            try:
                conn = sqlite3.connect(self.db_path)
                with lock:
                    connections.append(conn)
                cursor = conn.cursor()
                
                for _ in range(operations_per_thread):
                    records = self.generate_test_records(1)
                    cursor.execute(
                        """INSERT INTO biographical_data 
                           (name, birth_year, occupation) 
                           VALUES (:name, :birth_year, :occupation)""",
                        records[0]
                    )
                    conn.commit()
            except Exception as e:
                logger.error(f"Worker error: {e}")
                raise
            finally:
                if cursor:
                    cursor.close()
                if conn:
                    conn.close()

        threads = []
        start_time = time.time()
        
        try:
            threads = [threading.Thread(target=worker) for _ in range(num_threads)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()

            duration = time.time() - start_time
            total_operations = num_threads * operations_per_thread
            rate = total_operations / duration
            print(f"Completed {total_operations} operations in {duration:.2f} seconds")
            print(f"Rate: {rate:.2f} operations/second")
        finally:
            for t in threads:
                if t.is_alive():
                    t.join()

    @test_category('performance', 'storage')
    def test_database_size(self):
        """Test database size growth with different record counts."""
        print("\nTesting database size growth:")
        
        try:
            # Test with different record counts
            for record_count in [100, 500]:
                conn = None
                cursor = None
                try:
                    conn = sqlite3.connect(self.db_path)
                    cursor = conn.cursor()
                    
                    # Generate and store records
                    records = self.generate_test_records(record_count)  # Use instance method
                    start_time = time.time()
                    cursor.executemany(
                        """INSERT INTO biographical_data 
                           (name, birth_year, occupation) 
                           VALUES (:name, :birth_year, :occupation)""",
                        records
                    )
                    conn.commit()
                    duration = time.time() - start_time
                    
                    # Calculate and log metrics
                    rate = record_count / duration
                    logger.debug(f"Batch store rate: {rate:.2f} records/second")
                    
                    # Get database size
                    db_size = os.path.getsize(self.db_path) / 1024  # Convert to KB
                    avg_size = db_size / record_count
                    
                    print(f"Database with {record_count} records: {db_size:.2f} KB")
                    print(f"Average size per record: {avg_size:.2f} KB")
                    
                finally:
                    if cursor:
                        cursor.close()
                    if conn:
                        conn.close()
                    
        except Exception as e:
            logger.error(f"Error in database size test: {e}")
            raise

if __name__ == '__main__':
    unittest.main(verbosity=2)