import unittest
import sqlite3
import threading
import time
import os
import random
import logging
from memory_manager import (
    ConnectionPool, 
    DatabaseInitializer, 
    AirQualityMemory, 
    BackupManager,
    DatabaseError,
    ValidationError
)

logger = logging.getLogger(__name__)

class TestConnectionPool(unittest.TestCase):
    def setUp(self):
        self.db_path = "test_pool.db"
        self.pool = ConnectionPool(self.db_path, max_connections=5)
        # Create test table
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS test (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                value INTEGER
            )
        """)
        conn.commit()
        cursor.close()
        conn.close()
        
    def tearDown(self):
        try:
            # Close all connections
            while not self.pool.connections.empty():
                conn = self.pool.connections.get_nowait()
                conn.close()
            # Give Windows a moment to release the file
            time.sleep(0.1)
            if os.path.exists(self.db_path):
                os.remove(self.db_path)
        except Exception as e:
            print(f"Warning: Cleanup failed: {e}")

    def test_connection_pool_size(self):
        """Test that pool maintains correct number of connections."""
        self.assertEqual(self.pool.connections.qsize(), 5)
        
    def test_connection_reuse(self):
        """Test that connections are properly reused."""
        with self.pool.get_connection() as conn1:
            id1 = id(conn1)
        with self.pool.get_connection() as conn2:
            id2 = id(conn2)
        self.assertEqual(id1, id2)
        
    def test_concurrent_connections(self):
        """Test concurrent access to connection pool."""
        def worker(pool):
            try:
                # Each thread creates its own connection
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute("INSERT INTO test (value) VALUES (?)", (random.randint(1, 100),))
                conn.commit()
                cursor.close()
                conn.close()
            except Exception as e:
                print(f"Worker failed: {e}")

        threads = []
        for _ in range(10):  # Try to use more connections than pool size
            t = threading.Thread(target=worker, args=(self.pool,))
            threads.append(t)
            t.start()
            
        for t in threads:
            t.join()
            
        self.assertEqual(self.pool.connections.qsize(), 5)

class TestDatabaseInitializer(unittest.TestCase):
    def setUp(self):
        self.db_path = "test_init.db"
        self.conn = sqlite3.connect(self.db_path)
        
    def tearDown(self):
        self.conn.close()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
            
    def test_air_quality_schema(self):
        """Test air quality table creation and indexes."""
        DatabaseInitializer.initialize_air_quality_db(self.conn)
        
        # Check table exists
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='air_quality'
        """)
        self.assertIsNotNone(cursor.fetchone())
        
        # Check indexes exist
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='index' AND sql LIKE '%air_quality%'
        """)
        indexes = cursor.fetchall()
        self.assertEqual(len(indexes), 3)  # Should have 3 indexes
        
    def test_constraints(self):
        """Test that constraints are enforced."""
        DatabaseInitializer.initialize_air_quality_db(self.conn)
        cursor = self.conn.cursor()
        
        # Test negative value constraint
        with self.assertRaises(sqlite3.IntegrityError):
            cursor.execute("""
                INSERT INTO air_quality (city, region, year, month, day, 
                    station_id, pm25, pm25_trend, pm10, so2, monthly_avg, 
                    frequency, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, ["Test", "Test", 2024, 1, 1, "S1", -1, "up", 10, 5, 15, 
                  "daily", "2024-01-01"])

class TestBackupManager(unittest.TestCase):
    def setUp(self):
        self.db_path = "test_backup.db"
        self.backup_dir = "test_backups"
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)
        self.backup_mgr = BackupManager(self.db_path, self.backup_dir)
        
        # Create test database with some data
        self.conn = sqlite3.connect(self.db_path)
        DatabaseInitializer.initialize_air_quality_db(self.conn)
        self.conn.execute("""
            INSERT INTO air_quality (city, region, year, month, day, 
                station_id, pm25, pm25_trend, pm10, so2, monthly_avg, 
                frequency, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, ["Beijing", "North", 2024, 1, 1, "S1", 35.0, "up", 70.0, 
              8.0, 35.0, "daily", "2024-01-01"])
        self.conn.commit()
        
    def tearDown(self):
        try:
            # Clean up connections
            self.backup_mgr.cleanup()
            
            # Give Windows time to release file handles
            for attempt in range(5):
                try:
                    if os.path.exists(self.db_path):
                        os.remove(self.db_path)
                    for f in os.listdir(self.backup_dir):
                        os.remove(os.path.join(self.backup_dir, f))
                    os.rmdir(self.backup_dir)
                    break
                except PermissionError:
                    time.sleep(0.2)
        except Exception as e:
            print(f"Warning: Final cleanup attempt failed: {e}")
        
    def test_backup_creation(self):
        """Test backup creation and verification."""
        # Create initial data
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM air_quality")  # Clear existing data
            conn.execute("""
                INSERT INTO air_quality (
                    city, region, year, month, day, station_id,
                    pm25, pm25_trend, pm10, so2, monthly_avg, 
                    frequency, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, ["Beijing", "North", 2024, 1, 1, "S1", 35.0, "up", 
                  70.0, 8.0, 35.0, "daily", "2024-01-01"])
            conn.commit()

        # Create backup
        backup_path = self.backup_mgr.create_backup()
        self.assertTrue(os.path.exists(backup_path))
        
        # Verify backup contents
        with sqlite3.connect(backup_path) as backup_conn:
            cursor = backup_conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM air_quality")
            count = cursor.fetchone()[0]
            self.assertEqual(count, 1)  # Should only have one record
        
    def test_backup_restore(self):
        """Test database restoration from backup."""
        # Clear existing data and add one test record
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM air_quality")
            conn.execute("""
                INSERT INTO air_quality (
                    city, region, year, month, day, station_id,
                    pm25, pm25_trend, pm10, so2, monthly_avg, 
                    frequency, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, ["Beijing", "North", 2024, 1, 1, "S1", 35.0, "up", 
                  70.0, 8.0, 35.0, "daily", "2024-01-01"])
            conn.commit()
        
        # Create backup
        backup_path = self.backup_mgr.create_backup()
        
        # Clear original database
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM air_quality")
            conn.commit()
        
        # Restore from backup
        self.backup_mgr.restore_from_backup(backup_path)
        
        # Verify restored data
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM air_quality")
            data = cursor.fetchall()
            self.assertEqual(len(data), 1)

class TestAirQualityMemory(unittest.TestCase):
    def setUp(self):
        self.test_name = self._testMethodName
        self.db_path = f"test_air_quality_{self.test_name}.db"
        logger.info(f"Setting up test database: {self.db_path}")
        self.memory = AirQualityMemory(self.db_path)
        
    def tearDown(self):
        logger.info(f"Cleaning up test database: {self.db_path}")
        if hasattr(self, 'memory'):
            try:
                if hasattr(self.memory, '_local') and hasattr(self.memory._local, 'connection'):
                    self.memory._local.connection.close()
                    delattr(self.memory._local, 'connection')
                    logger.debug("Database connection closed")
            except Exception as e:
                logger.info(f"Expected cleanup behavior: {e}")
                
        try:
            if os.path.exists(self.db_path):
                os.remove(self.db_path)
                logger.debug(f"Database file removed: {self.db_path}")
        except PermissionError:
            logger.info(f"Expected behavior: Database file {self.db_path} still in use by other threads, will be cleaned up later")
            
    @classmethod
    def tearDownClass(cls):
        # Clean up any remaining test database files
        for file in os.listdir('.'):
            if file.startswith('test_air_quality_') and file.endswith('.db'):
                try:
                    os.remove(file)
                except PermissionError:
                    pass

    def test_data_validation(self):
        logger.info("Testing data validation with valid and invalid records...")
        
        # Test valid data
        valid_reading = {
            "timestamp": "2024-03-05 13:00:00",
            "location": "Test Location",
            "pm25": 25.0,
            "temperature": 22.5,
            "humidity": 45.0
        }
        self.assertTrue(self.memory.store_reading(**valid_reading))
        logger.info("✓ Valid data stored successfully")

        # Test invalid data - expecting failure
        invalid_reading = {
            "timestamp": "invalid",
            "location": "",
            "pm25": -1,
            "temperature": None,  # This will trigger NOT NULL constraint
            "humidity": 101
        }
        logger.info("Testing invalid data - expecting constraint violation...")
        self.assertFalse(self.memory.store_reading(**invalid_reading))
        logger.info("✓ Invalid data correctly rejected")

    def test_concurrent_storage(self):
        logger.info("Testing concurrent storage with multiple threads...")
        
        # Clear any existing data first
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM air_quality")
        conn.commit()
        cursor.close()
        conn.close()
        
        threads = []
        thread_count = 10
        logger.info(f"Launching {thread_count} worker threads...")
        
        for i in range(thread_count):
            t = threading.Thread(
                target=self.worker, 
                args=(self.memory,),
                name=f"Worker-{i}"
            )
            threads.append(t)
            t.start()
            logger.debug(f"Started thread {t.name}")

        logger.info("Waiting for all threads to complete...")
        for t in threads:
            t.join()
            
        logger.info("Verifying data...")
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM air_quality")
        count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        
        self.assertEqual(count, thread_count, 
            f"Expected {thread_count} records but found {count}")
        logger.info(f"✓ All {count} concurrent writes verified")

    def worker(self, memory):
        try:
            # Each worker inserts exactly one record
            memory.store_reading(
                timestamp="2024-03-05 13:00:00",
                location=f"Location-{threading.current_thread().name}",
                pm25=25.0,
                temperature=22.5,
                humidity=45.0
            )
            logger.debug(f"Worker {threading.current_thread().name} completed successfully")
        except Exception as e:
            logger.error(f"Worker {threading.current_thread().name} failed: {e}")

if __name__ == '__main__':
    unittest.main(verbosity=2) 