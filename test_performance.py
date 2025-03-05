import unittest
import time
import random
import string
import os
import threading
import logging
from memory_manager import BiographicalMemory
from performance_metrics import PerformanceMetrics

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

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
        cls.metrics = PerformanceMetrics()
        if os.path.exists(cls.test_db):
            os.remove(cls.test_db)
        cls.memory = BiographicalMemory(cls.test_db)
        logger.debug("Test class setup complete")

    def setUp(self):
        """Set up test database."""
        self.metrics.start_test_run()

    def tearDown(self):
        """Clean up after each test."""
        self.metrics.save_metrics()

    @classmethod
    def tearDownClass(cls):
        """Clean up class-level resources."""
        if cls.memory:
            cls.memory.close()
        cls.metrics.print_comparison()
        # Give time for Windows to release file handles
        for _ in range(5):
            try:
                if os.path.exists(cls.test_db):
                    os.remove(cls.test_db)
                break
            except PermissionError:
                time.sleep(0.2)
        logger.debug("Test class teardown complete")

    def generate_test_data(self, size):
        """Generate test data without creating connections."""
        occupations = ['Engineer', 'Doctor', 'Teacher', 'Artist']
        return [{
            'name': f'Person_{i}',
            'age': random.randint(18, 90),
            'occupation': occupations[i % len(occupations)],
            'background': f'Background for person {i}'
        } for i in range(size)]

    def test_insertion_performance(self):
        """Test performance of inserting records."""
        print("\nTesting insertion performance:")
        batch_sizes = [10, 100, 1000]
        
        for size in batch_sizes:
            # Generate test data first
            people = self.generate_test_data(size)
            
            # Test individual inserts
            start_time = time.time()
            for person in people:
                self.memory.store(person['name'], person)
            duration = time.time() - start_time
            rate = size / duration
            print(f"Individual inserts: {size} records in {duration:.2f} seconds")
            print(f"Rate: {rate:.2f} records/second")
            self.metrics.log_metric('insertion_rates', rate, size)

            # Generate new test data for batch insert
            people = self.generate_test_data(size)
            
            # Test batch insert
            start_time = time.time()
            self.memory.batch_store(people)
            duration = time.time() - start_time
            rate = size / duration
            print(f"Batch insert: {size} records in {duration:.2f} seconds")
            print(f"Rate: {rate:.2f} records/second")
            self.metrics.log_metric('insertion_rates', rate, size)

    def test_retrieval_performance(self):
        """Test performance of retrieving records."""
        print("\nTesting retrieval performance:")
        # Create test data
        test_data = self.generate_random_person()
        person_id = self.memory.store(test_data['name'], test_data)
        
        # Test single record retrieval
        start_time = time.time()
        for _ in range(100):
            person = self.memory.retrieve(person_id)
        end_time = time.time()
        duration = end_time - start_time
        rate = 100 / duration
        print(f"Retrieved 100 records in {duration:.2f} seconds")
        print(f"Rate: {rate:.2f} retrievals/second")

    def test_query_performance(self):
        """Test performance of different query patterns."""
        print("\nTesting query performance:")
        start_time = time.time()
        people_list = self.memory.get_all_people()
        duration = time.time() - start_time
        print(f"Listed all {len(people_list)} people in {duration:.2f} seconds")

    def test_concurrent_performance(self):
        logger.debug("Starting concurrent performance test")
        num_threads = 10
        operations_per_thread = 200
        threads = []
        start_time = time.time()

        def worker():
            for _ in range(operations_per_thread):
                try:
                    person = self.generate_random_person()
                    self.memory.store(person['name'], person)
                except Exception as e:
                    logger.error(f"Error in worker thread: {e}")

        # Start threads
        for _ in range(num_threads):
            t = threading.Thread(target=worker)
            t.daemon = True  # Make threads daemon so they don't hang
            t.start()
            threads.append(t)

        # Wait for threads with timeout
        for t in threads:
            t.join(timeout=30)  # 30 second timeout per thread

        duration = time.time() - start_time
        total_operations = num_threads * operations_per_thread
        rate = total_operations / duration
        print(f"\nPerformed {total_operations} concurrent operations in {duration:.2f} seconds")
        print(f"Rate: {rate:.2f} operations/second")

    def test_database_size(self):
        """Test database size growth."""
        print("\nTesting database size growth:")
        sizes = [100, 500, 1000]
        
        for size in sizes:
            # Create fresh database for each size test
            if hasattr(self, 'memory'):
                self.memory.close()
                self.memory = None
                # Give time for Windows to release file handles
                for _ in range(5):
                    try:
                        if os.path.exists(self.test_db):
                            os.remove(self.test_db)
                        break
                    except PermissionError:
                        time.sleep(0.2)
            
            self.memory = BiographicalMemory(self.test_db)
            
            # Insert records
            for _ in range(size):
                person = generate_random_person()
                self.memory.store(person['name'], person)
            
            db_size = os.path.getsize(self.test_db) / 1024  # Size in KB
            print(f"Database with {size} records: {db_size:.2f} KB")
            print(f"Average size per record: {db_size/size:.2f} KB")

    @staticmethod
    def generate_random_person():
        """Generate random biographical data for testing."""
        def random_string(length=10):
            return ''.join(random.choices(string.ascii_letters, k=length))
        
        return {
            'name': random_string(),
            'age': random.randint(18, 90),
            'occupation': random_string(),
            'bio': random_string(50)
        }

if __name__ == '__main__':
    unittest.main(verbosity=2) 