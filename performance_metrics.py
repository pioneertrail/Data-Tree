import json
import time
from datetime import datetime
import os

class PerformanceMetrics:
    def __init__(self, filename="performance_history.json"):
        self.filename = filename
        self.current_metrics = self._create_empty_metrics()

    def _create_empty_metrics(self):
        """Create an empty metrics dictionary."""
        return {
            'timestamp': None,
            'insertion_rates': [],
            'retrieval_rates': [],
            'query_rates': [],
            'concurrent_rates': [],
            'database_sizes': [],
            'average_response_times': {}
        }

    def log_metric(self, category, value, batch_size=None):
        """Log a performance metric with optional batch size."""
        if batch_size:
            self.current_metrics[category].append({
                'batch_size': batch_size,
                'rate': value
            })
        else:
            self.current_metrics[category].append(value)

    def start_test_run(self):
        """Start a new test run."""
        self.current_metrics = self._create_empty_metrics()
        self.current_metrics['timestamp'] = datetime.now().isoformat()

    def save_metrics(self):
        """Save current metrics to file."""
        history = []
        if os.path.exists(self.filename):
            with open(self.filename, 'r') as f:
                try:
                    history = json.load(f)
                except json.JSONDecodeError:
                    history = []
        
        history.append(self.current_metrics)
        
        with open(self.filename, 'w') as f:
            json.dump(history, f, indent=2)

    def print_comparison(self):
        """Print comparison with previous test runs."""
        if not os.path.exists(self.filename):
            print("\nNo previous test runs to compare")
            return

        with open(self.filename, 'r') as f:
            try:
                history = json.load(f)
            except json.JSONDecodeError:
                print("\nNo valid previous test runs to compare")
                return

        if len(history) < 2:
            print("\nNeed at least two test runs to compare")
            return

        current = history[-1]
        previous = history[-2]

        print("\nPerformance Comparison with Previous Run:")
        print("----------------------------------------")
        
        # Compare insertion rates
        try:
            for curr, prev in zip(current['insertion_rates'], previous['insertion_rates']):
                batch_size = curr['batch_size']
                change = ((curr['rate'] - prev['rate']) / prev['rate']) * 100
                print(f"Insertion Rate (batch size {batch_size}): "
                      f"{curr['rate']:.2f} ops/sec "
                      f"({'↑' if change > 0 else '↓'}{abs(change):.1f}%)")
        except (KeyError, IndexError, ZeroDivisionError):
            print("Could not compare insertion rates")

        # Compare retrieval rates
        try:
            for curr, prev in zip(current['retrieval_rates'], previous['retrieval_rates']):
                change = ((curr - prev) / prev) * 100
                print(f"Retrieval Rate: {curr:.2f} ops/sec "
                      f"({'↑' if change > 0 else '↓'}{abs(change):.1f}%)")
        except (KeyError, IndexError, ZeroDivisionError):
            print("Could not compare retrieval rates")

        # Compare concurrent operation rates
        try:
            if current['concurrent_rates'] and previous['concurrent_rates']:
                curr_concurrent = current['concurrent_rates'][-1]
                prev_concurrent = previous['concurrent_rates'][-1]
                change = ((curr_concurrent - prev_concurrent) / prev_concurrent) * 100
                print(f"Concurrent Operation Rate: {curr_concurrent:.2f} ops/sec "
                      f"({'↑' if change > 0 else '↓'}{abs(change):.1f}%)")
        except (KeyError, IndexError, ZeroDivisionError):
            print("Could not compare concurrent operation rates") 