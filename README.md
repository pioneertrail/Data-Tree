# ZeroLag - High-Performance Pattern Engine

ZeroLag is a high-performance pattern storage and analysis engine built with Flask, featuring real-time visualization and customizable styling.

![ZeroLag Interface](docs/images/interface.png)

## Features

- 🚀 High-speed binary pattern storage and retrieval
- 📊 Real-time performance metrics and visualizations
- 🎨 Customizable dark-mode interface
- 📈 Pattern analysis and distribution tracking
- ⚡ Quick pattern operations
- 🔄 Dynamic CSS theme support

## Quick Start

```bash
# Clone the repository
git clone https://github.com/yourusername/zerolag.git
cd zerolag

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py
```

Visit `http://127.0.0.1:5000` in your browser.

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

## Performance Characteristics

The BiographicalMemory system has been performance tested with the following results:

### Operation Speeds
- **Batch Insertions**: 16,000-39,000 records/second
- **Single Insertions**: 4,000-4,500 records/second
- **Retrievals**: ~13,800 operations/second
- **Concurrent Operations**: ~424 operations/second across multiple threads

### Storage Efficiency
- Average storage per record: 0.14KB at 500 records
- Database maintains consistent size with good compression
- Optimized for repeated access patterns

### Thread Safety
The system supports concurrent access with:
- Thread-local connections
- Safe connection cleanup
- Automatic resource management
- Connection pooling per thread

### Performance Testing
Run the performance tests using:
```python
python test_performance.py
```

Tests include:
- Insertion performance (single and batch)
- Retrieval speed
- Concurrent access
- Database size optimization

### Optimization Features
- WAL journaling mode
- Memory-mapped I/O
- Optimized cache settings
- Index on name field for fast lookups

## Running Tests

### Quick Start
To run all tests with the colored output:
```python -m tests.test_runner```

### Test Output
The test runner provides:
- Real-time colored status indicators (✓ for pass, ✗ for fail)
- Detailed debug and performance metrics during test execution
- Summary statistics showing total tests and pass/fail counts
- Organized breakdown of tests by class

### Test Organization
Tests are organized into several categories:
- BiographicalMemory: Core database operations and concurrency
- AirQualityMemory: Specialized data validation and storage
- BackupManager: Database backup and restore functionality
- ConnectionPool: Connection management and pooling
- DatabaseInitializer: Schema and constraint management
- Performance: Database operation benchmarks and scaling tests

### Debug Output
Debug messages are preserved in the output to help diagnose:
- Database initialization and cleanup
- Connection management
- Performance metrics
- Concurrent operation behavior

Would you like me to:
1. Create a separate TESTING.md with more detailed documentation?
2. Add examples of common testing scenarios?
3. Include troubleshooting tips?

Let me know which aspects you'd like to focus on in the documentation! 