# API Documentation

## BiographicalMemory

### Constructor
```python
BiographicalMemory(db_path: str)
```
Initializes a new biographical memory database.

#### Parameters
- `db_path`: Path to the SQLite database file

### Methods

#### store
```python
store(name: str, data: dict) -> int
```
Stores biographical data in the database.

##### Parameters
- `name`: Person's name
- `data`: Dictionary containing biographical data
  - `age`: int
  - `occupation`: str
  - `bio`: str

##### Returns
- `int`: ID of the stored record

#### retrieve
```python
retrieve(person_id: int) -> dict
```
Retrieves biographical data by ID.

##### Parameters
- `person_id`: ID of the person to retrieve

##### Returns
- `dict`: Biographical data or None if not found

#### close
```python
close()
```
Closes all database connections safely. 