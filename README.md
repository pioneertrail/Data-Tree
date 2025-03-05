# Biographical Memory Database

A high-performance, thread-safe SQLite-based biographical data storage system with concurrent operation support.

## Features
- Thread-safe database operations
- Connection pooling with thread-local storage
- Comprehensive performance testing suite
- Support for concurrent operations
- Efficient biographical data storage and retrieval

## Installation
```bash
git clone https://github.com/yourusername/biographical-memory
cd biographical-memory
pip install -r requirements.txt
```

## Usage
```python
from memory_manager import BiographicalMemory

# Initialize the database
memory = BiographicalMemory("biographical_data.db")

# Store biographical data
person_data = {
    'name': 'John Doe',
    'age': 30,
    'occupation': 'Engineer',
    'bio': 'Experienced software developer...'
}
person_id = memory.store(person_data['name'], person_data)

# Retrieve biographical data
person = memory.retrieve(person_id)

# Clean up
memory.close()
```

## Performance Metrics
- Concurrent Operations: ~2,000 ops/sec
- Single-thread Retrieval: ~1,285 ops/sec
- Batch Insert (1000 records): ~34,000 ops/sec

## Testing
Run the test suite:
```bash
python test_performance.py
```

## Project Structure

- `tree_node.py`: Base tree data structure implementation
- `memory_manager.py`: Memory system for storing and retrieving data
- `air_quality_agent.py`: Main agent class for data loading and querying

## Usage

1. Initialize the agent with a dataset:
```python
from air_quality_agent import AirQualityAgent

agent = AirQualityAgent("path/to/air_quality.csv")
```

2. Query data:
```python
# Get PM2.5 level
result = agent.query("What is the PM2.5 level?")

# Get historical data
history = agent.get_historical_data("2020-01-01", "2020-12-31")

# Analyze trends
trends = agent.analyze_trends("PM2.5", days=30)
```

## Data Structure

The memory system uses a hierarchical tree structure with bit-mapped navigation:

- Root (11100000)
  - Metadata (11000000)
    - City
    - Date
    - Station ID
  - Pollutant Levels (10101000)
    - PM2.5
    - PM10
    - SO2
  - Aggregates (11100000)
    - Average PM2.5

## License

MIT License 