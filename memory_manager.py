import os
import sqlite3
from datetime import datetime
import time
import threading
from contextlib import contextmanager
import logging
from typing import List, Dict, Optional, Any, Set

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
        self.metrics = {'store': [], 'retrieve': [], 'batch': []}
        self._initialize_db()

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
        cursor.execute("""
            SELECT * FROM sqlite_master 
            WHERE type='table' AND name='biographies'
        """)
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
        except Exception as e:
            logger.error(f"Store failed: {e}")
            raise

    def retrieve(self, name, field):
        """Retrieve a specific field for a person."""
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
            cursor.execute(f"SELECT {field} FROM biographies WHERE name = ?", (name,))
            result = cursor.fetchone()
            return result[0] if result else None
        except Exception as e:
            logger.error(f"Retrieve failed: {e}")
            return None
    
    def batch_store(self, records):
        """Store multiple records in a batch."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            start_time = time.time()
            
            cursor.executemany("""
                INSERT OR REPLACE INTO biographies
                (name, birth_year, birth_place, death_year, death_place,
                occupation, achievement, education, nationality, known_for)
                VALUES (:name, :birth_year, :birth_place, :death_year, :death_place,
                :occupation, :achievement, :education, :nationality, :known_for)
            """, records)
            
            conn.commit()
            duration = time.time() - start_time
            rate = len(records) / duration if duration > 0 else 0
            logger.debug(f"Batch store rate: {rate:.2f} records/second")
            
            # Get the IDs of inserted records
            cursor.execute("SELECT last_insert_rowid()")
            last_id = cursor.fetchone()[0]
            return list(range(last_id - len(records) + 1, last_id + 1))
        except Exception as e:
            logger.error(f"Batch store failed: {e}")
            raise

    def batch_retrieve(self, ids):
        """Retrieve multiple records by their IDs."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            placeholders = ','.join('?' * len(ids))
            cursor.execute(f"""
                SELECT * FROM biographies 
                WHERE rowid IN ({placeholders})
            """, ids)
            return cursor.fetchall()
        except Exception as e:
            logger.error(f"Batch retrieve failed: {e}")
        return None
    
    def get_all_people(self):
        """Retrieve all records from the database."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM biographies")
            return cursor.fetchall()
        except Exception as e:
            logger.error(f"Get all people failed: {e}")
            return []

    def optimize_size(self):
        """Optimize database size."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("VACUUM")
            conn.commit()
        except Exception as e:
            logger.error(f"Size optimization failed: {e}")
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
        for conn in self.connections.values():
            conn.close()
        self.connections.clear()
        logger.debug("Closed all connections")

    def get_performance_metrics(self):
        """Get average performance metrics."""
        store_rate = sum(self.metrics['store']) / len(self.metrics['store']) if self.metrics['store'] else 0
        retrieve_rate = sum(self.metrics['retrieve']) / len(self.metrics['retrieve']) if self.metrics['retrieve'] else 0
        return {'store_rate': store_rate, 'retrieve_rate': retrieve_rate}

class AirQualityMemory:
    def __init__(self, db_path=":memory:"):
        """Initialize the air quality memory system.
        
        Args:
            db_path (str): Path to SQLite database file
        """
        self.db_path = db_path
        self.connection = self._create_connection()
        self._initialize_db()

    def _create_connection(self):
        """Create an optimized SQLite connection."""
        connection = sqlite3.connect(self.db_path)
        connection.execute("PRAGMA journal_mode=WAL")  # Write-Ahead Logging
        connection.execute("PRAGMA synchronous=NORMAL")  # Faster synchronization
        connection.execute("PRAGMA cache_size=-64000")  # 64MB cache
        connection.execute("PRAGMA temp_store=MEMORY")  # Store temp tables in memory
        return connection

    def _initialize_db(self):
        """Initialize the database schema."""
        cursor = self.connection.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS air_quality (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                city TEXT NOT NULL,
                region TEXT NOT NULL,
                year INTEGER NOT NULL,
                month INTEGER NOT NULL,
                day INTEGER NOT NULL,
                station_id TEXT NOT NULL,
                pm25 REAL,
                pm25_trend TEXT,
                pm10 REAL,
                so2 REAL,
                monthly_avg REAL,
                frequency TEXT,
                timestamp TEXT NOT NULL
            )
        """)
        self.connection.commit()

    def store(self, data_string, timestamp):
        """Store air quality data.
        
        Args:
            data_string (str): Comma-separated data string
            timestamp (str): ISO format timestamp
        """
        # Parse data string
        parts = data_string.split(',')
        if len(parts) != 12:
            raise ValueError("Invalid data string format")

        cursor = self.connection.cursor()
        cursor.execute("""
            INSERT INTO air_quality (
                city, region, year, month, day, station_id,
                pm25, pm25_trend, pm10, so2, monthly_avg, frequency,
                timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, parts + [timestamp])
        self.connection.commit()

    def retrieve(self, path):
        """Retrieve data based on query path.
        
        Args:
            path (list): Query path components
            
        Returns:
            str: Query result
        """
        cursor = self.connection.cursor()
        
        if path[0] == "Pollutant Levels":
            pollutant = path[1].lower().replace('.', '')
            cursor.execute(f"""
                SELECT {pollutant}, timestamp 
                FROM air_quality 
                ORDER BY timestamp DESC 
                LIMIT 1
            """)
            result = cursor.fetchone()
            return f"Latest {path[1]} level: {result[0]}" if result else "No recent data available"

        elif path[0] == "Aggregates":
            cursor.execute("""
                SELECT AVG(pm25) 
                FROM air_quality
            """)
            result = cursor.fetchone()
            avg_value = result[0] if result and result[0] is not None else 0
            return f"Average PM2.5 level: {avg_value:.2f}"

        elif path[0] == "Metadata":
            if path[1] == "City":
                cursor.execute("SELECT DISTINCT city FROM air_quality")
                cities = cursor.fetchall()
                return "Monitored cities: " + ", ".join(city[0] for city in cities) if cities else "No cities monitored"
            elif path[1] == "Date":
                cursor.execute("SELECT timestamp FROM air_quality ORDER BY timestamp DESC LIMIT 1")
                result = cursor.fetchone()
                return f"Latest data from: {result[0]}" if result else "No data available"

        elif path[0] == "Trends":
            cursor.execute("""
                SELECT pm25_trend, timestamp 
                FROM air_quality 
                ORDER BY timestamp DESC 
                LIMIT 1
            """)
            result = cursor.fetchone()
            return f"Current PM2.5 trend: {result[0]}" if result else "No trend data available"

        elif path[0] == "City Data":
            city = path[1]
            cursor.execute("""
                SELECT pm25, pm10, so2, timestamp 
                FROM air_quality 
                WHERE city = ? 
                ORDER BY timestamp DESC 
                LIMIT 1
            """, (city,))
            result = cursor.fetchone()
            if result:
                return (f"Air quality in {city}:\n"
                       f"  PM2.5: {result[0]:.1f} µg/m³\n"
                       f"  PM10:  {result[1]:.1f} µg/m³\n"
                       f"  SO2:   {result[2]:.1f} µg/m³\n"
                       f"As of: {result[3]}")
            return f"No recent data available for {city}"

        return "No data found for that query"
    
    def get_history(self, start_date=None, end_date=None):
        """Retrieve historical data within a date range.
        
        Args:
            start_date (str, optional): Start date in ISO format
            end_date (str, optional): End date in ISO format
            
        Returns:
            list: Historical data points
        """
        cursor = self.connection.cursor()
        query = "SELECT * FROM air_quality"
        params = []
        
        if start_date or end_date:
            query += " WHERE "
            if start_date:
                query += "timestamp >= ?"
                params.append(start_date)
            if end_date:
                query += " AND " if start_date else ""
                query += "timestamp <= ?"
                params.append(end_date)
                
        query += " ORDER BY timestamp"
        cursor.execute(query, params)
        return cursor.fetchall() 