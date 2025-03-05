import unittest
import sqlite3
import os
from memory_manager import BiographicalMemory

class TestBiographicalMemory(unittest.TestCase):
    def setUp(self):
        """Set up a fresh test database before each test."""
        self.test_db = "test_bio_memory.db"
        # Remove existing test database if it exists
        if os.path.exists(self.test_db):
            try:
                os.remove(self.test_db)
            except PermissionError:
                pass
        self.memory = BiographicalMemory(self.test_db)
        
        # Sample test data
        self.turing_data = {
            'name': 'Alan Turing',
            'birth_year': 1912,
            'birth_place': 'London, England',
            'death_year': 1954,
            'death_place': 'Wilmslow, England',
            'occupation': 'Computer Scientist and Mathematician',
            'achievement': 'Developed the Turing machine and broke the Enigma code',
            'nationality': 'British',
            'known_for': 'Being the father of computer science and artificial intelligence'
        }
        
    def tearDown(self):
        """Clean up after each test."""
        if os.path.exists(self.test_db):
            try:
                os.remove(self.test_db)
            except PermissionError:
                pass

    def test_database_creation(self):
        """Test that database and table are created correctly."""
        conn = sqlite3.connect(self.test_db)
        cursor = conn.cursor()
        
        # Check if biographies table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='biographies'
        """)
        self.assertIsNotNone(cursor.fetchone())
        
        # Check table schema
        cursor.execute("PRAGMA table_info(biographies)")
        columns = {row[1] for row in cursor.fetchall()}
        expected_columns = {
            'name', 'birth_year', 'birth_place', 'death_year',
            'death_place', 'occupation', 'achievement',
            'education', 'nationality', 'known_for'
        }
        self.assertEqual(columns, expected_columns)
        
        conn.close()

    def test_store_and_retrieve(self):
        """Test storing and retrieving biographical data."""
        # Store data
        self.memory.store('Alan Turing', self.turing_data)
        
        # Test retrieving specific fields
        self.assertEqual(
            self.memory.retrieve('Alan Turing', 'birth_year'),
            1912
        )
        self.assertEqual(
            self.memory.retrieve('Alan Turing', 'nationality'),
            'British'
        )
        
        # Test retrieving non-existent person
        self.assertIsNone(
            self.memory.retrieve('Nonexistent Person', 'birth_year')
        )

    def test_update_existing_record(self):
        """Test updating an existing record."""
        # Store initial data
        self.memory.store('Alan Turing', self.turing_data)
        
        # Update single field
        updated_data = self.turing_data.copy()
        updated_data['achievement'] = 'Updated achievement'
        self.memory.store('Alan Turing', updated_data)
        
        # Verify update
        self.assertEqual(
            self.memory.retrieve('Alan Turing', 'achievement'),
            'Updated achievement'
        )

    def test_database_persistence(self):
        """Test that data persists after reopening database."""
        # Store data
        self.memory.store('Alan Turing', self.turing_data)
        
        # Create new connection to simulate program restart
        new_memory = BiographicalMemory(self.test_db)
        
        # Verify data persisted
        self.assertEqual(
            new_memory.retrieve('Alan Turing', 'birth_year'),
            1912
        )

    def test_invalid_inputs(self):
        """Test handling of invalid inputs."""
        # Test None values
        with self.assertRaises(ValueError):
            self.memory.store(None, self.turing_data)
        
        # Test empty name
        with self.assertRaises(ValueError):
            self.memory.store('', self.turing_data)
        
        # Test invalid field name
        self.assertIsNone(
            self.memory.retrieve('Alan Turing', 'nonexistent_field')
        )

    def test_multiple_records(self):
        """Test handling multiple records."""
        # Additional test data
        lovelace_data = {
            'name': 'Ada Lovelace',
            'birth_year': 1815,
            'birth_place': 'London, England',
            'death_year': 1852,
            'occupation': 'Mathematician',
            'nationality': 'British'
        }
        
        # Store multiple records
        self.memory.store('Alan Turing', self.turing_data)
        self.memory.store('Ada Lovelace', lovelace_data)
        
        # Test retrieving from both records
        self.assertEqual(
            self.memory.retrieve('Alan Turing', 'birth_year'),
            1912
        )
        self.assertEqual(
            self.memory.retrieve('Ada Lovelace', 'birth_year'),
            1815
        )

    def test_concurrent_access(self):
        """Test database handles concurrent access correctly."""
        import threading
        
        def store_data():
            memory = BiographicalMemory(self.test_db)
            memory.store('Alan Turing', self.turing_data)
        
        threads = [threading.Thread(target=store_data) for _ in range(5)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        
        # Verify data integrity
        self.assertEqual(
            self.memory.retrieve('Alan Turing', 'birth_year'),
            1912
        )

if __name__ == '__main__':
    unittest.main(verbosity=2) 