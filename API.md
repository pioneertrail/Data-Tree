# API Documentation

## Overview

The Performance Tests Dashboard provides a RESTful API for managing test results. All responses are in JSON format.

## Endpoints

### Get All Results

Retrieves the 10 most recent test results across all test types.

```http
GET /api/results
```

#### Response

```json
[
  {
    "id": 1,
    "test_type": "speed",
    "response_time": 75,
    "memory_usage": 156,
    "ops_per_sec": 982,
    "timestamp": "2024-03-06 13:05:39"
  },
  // ... more results
]
```

### Get Results by Test Type

Retrieves the 5 most recent results for a specific test type.

```http
GET /api/results/<test_type>
```

#### Parameters

- `test_type`: The type of test (speed, memory, or load)

#### Response

```json
[
  {
    "id": 1,
    "test_type": "speed",
    "response_time": 75,
    "memory_usage": 156,
    "ops_per_sec": 982,
    "timestamp": "2024-03-06 13:05:39"
  },
  // ... more results
]
```

### Save Test Result

Saves a new test result to the database.

```http
POST /api/results
Content-Type: application/json
```

#### Request Body

```json
{
  "test_type": "speed",
  "response_time": 75,
  "memory_usage": 156,
  "ops_per_sec": 982
}
```

#### Response

```json
{
  "id": 1,
  "test_type": "speed",
  "response_time": 75,
  "memory_usage": 156,
  "ops_per_sec": 982,
  "timestamp": "2024-03-06 13:05:39"
}
```

## Data Models

### TestResult

| Field         | Type      | Description                               |
|---------------|-----------|-------------------------------------------|
| id            | Integer   | Unique identifier                         |
| test_type     | String    | Type of test (speed, memory, load)       |
| response_time | Integer   | Response time in milliseconds             |
| memory_usage  | Integer   | Memory usage in MB                        |
| ops_per_sec   | Integer   | Operations per second                     |
| timestamp     | DateTime  | When the test was conducted              |

## Error Handling

The API uses standard HTTP status codes:

- `200 OK`: Successful request
- `400 Bad Request`: Invalid request body or parameters
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

Error responses include a message:

```json
{
  "error": "Description of what went wrong"
}
```

## Rate Limiting

Currently, there are no rate limits implemented on the API endpoints.

## Examples

### JavaScript Fetch

```javascript
// Get all results
fetch('/api/results')
  .then(response => response.json())
  .then(data => console.log(data));

// Save a result
fetch('/api/results', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    test_type: 'speed',
    response_time: 75,
    memory_usage: 156,
    ops_per_sec: 982
  })
})
  .then(response => response.json())
  .then(data => console.log(data));
```

### Python Requests

```python
import requests

# Get results for a specific test type
response = requests.get('http://127.0.0.1:5000/api/results/speed')
results = response.json()

# Save a new result
data = {
    'test_type': 'speed',
    'response_time': 75,
    'memory_usage': 156,
    'ops_per_sec': 982
}
response = requests.post('http://127.0.0.1:5000/api/results', json=data)
result = response.json()
``` 