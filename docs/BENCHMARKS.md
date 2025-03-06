# Performance Benchmarks

## Latest Benchmarks (v1.1.0)

### Single Operations
| Operation | Rate (ops/sec) | Latency (ms) |
|-----------|---------------|--------------|
| Retrieve  | 1,274        | 0.78        |
| Store     | 954          | 1.05        |
| Search    | 865          | 1.16        |

### Batch Operations
| Batch Size | Store (records/sec) | Retrieve (records/sec) |
|------------|-------------------|---------------------|
| 10         | 4,087            | 3,254               |
| 100        | 20,805           | 15,632              |
| 1000       | 34,253           | 28,765              |

### Resource Usage
| Records | Database Size | Memory Usage |
|---------|--------------|--------------|
| 100     | 36 KB       | 2.4 MB      |
| 500     | 120 KB      | 3.8 MB      |
| 1000    | 204 KB      | 5.2 MB      |

### Concurrent Operations
- 10 threads: 2,702 operations/second
- 20 threads: 2,543 operations/second
- 50 threads: 2,187 operations/second

## Optimization Settings
```sql
PRAGMA journal_mode = WAL
PRAGMA synchronous = NORMAL
PRAGMA cache_size = -64000
PRAGMA temp_store = MEMORY
PRAGMA mmap_size = 64000000
PRAGMA page_size = 4096
```

## Environment
- Python 3.13
- SQLite 3
- Windows 11 