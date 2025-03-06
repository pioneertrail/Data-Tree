# ZeroLag - Cursor Development Guide

## 🚀 Quick Setup in Cursor

1. Clone and open in Cursor:
```bash
git clone https://github.com/yourusername/zerolag.git
cd zerolag
cursor .
```

2. Install dependencies:
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## 🗺️ Project Map

### Core Components

```python
# app.py - Main Application Entry
from flask import Flask, render_template, request, jsonify
from src.binary_storage import HighSpeedBinaryStorage

# Key routes:
@app.route('/')  # Main interface
@app.route('/visualizations')  # Visualization dashboard
@app.route('/query', methods=['POST'])  # Pattern operations
@app.route('/generate_viz/<viz_type>')  # Generate visualizations
```

```python
# src/binary_storage.py - Pattern Storage Engine
class HighSpeedBinaryStorage:
    def store(self, name: str, pattern: str) -> bool
    def retrieve(self, name: str) -> str
    def list_all(self) -> list 