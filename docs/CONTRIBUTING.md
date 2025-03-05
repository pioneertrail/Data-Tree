# Contributing to Biographical Memory Database

## Development Setup
1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/yourusername/biographical-memory
   ```
3. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # or `venv\Scripts\activate` on Windows
   ```
4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Testing
- Run all tests:
  ```bash
  python -m unittest discover tests
  ```
- Run performance tests:
  ```bash
  python tests/test_performance.py
  ```

## Code Style
- Follow PEP 8 guidelines
- Use type hints
- Add docstrings for all public methods
- Keep methods focused and single-purpose

## Pull Request Process
1. Create a feature branch
2. Add tests for new functionality
3. Update documentation
4. Submit PR with clear description
5. Wait for review

## Performance Considerations
- Monitor thread safety
- Test with concurrent operations
- Profile memory usage
- Benchmark against previous versions 