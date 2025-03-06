import unittest
import sys
import time
import argparse
import logging
import yaml
from pathlib import Path
from collections import defaultdict
from colorama import init, Fore, Style
from functools import wraps
from typing import List, Set

# Initialize colorama for Windows support
init()

def load_config():
    config_path = Path(__file__).parent / 'test_config.yaml'
    default_config = {
        'output': {
            'quiet': False,
            'verbose': False,
            'no_color': False,
            'show_docstrings': True
        },
        'timing': {
            'slow_test_threshold': 1.0,
            'show_class_timing': True,
            'warn_on_slow': True
        },
        'logging': {
            'level': 'INFO',
            'format': '%(levelname)s:%(name)s:%(message)s'
        },
        'patterns': {
            'test_files': 'test_*.py',
            'exclude': []
        }
    }

    if config_path.exists():
        with open(config_path) as f:
            return {**default_config, **yaml.safe_load(f)}
    return default_config

def parse_args(config):
    parser = argparse.ArgumentParser(description='Run tests with enhanced output control')
    parser.add_argument('-q', '--quiet', action='store_true',
                       default=config['output']['quiet'],
                       help='Suppress debug output')
    parser.add_argument('-v', '--verbose', action='store_true',
                       default=config['output']['verbose'],
                       help='Show more detailed output')
    parser.add_argument('--no-color', action='store_true',
                       default=config['output']['no_color'],
                       help='Disable colored output')
    parser.add_argument('--config', type=str,
                       help='Path to custom config file')
    parser.add_argument('--category', '-c', action='append',
                       help='Run only tests with specific category')
    return parser.parse_args()

def test_category(*categories):
    """Decorator to assign categories to test methods"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        wrapper.test_categories = set(categories)
        return wrapper
    return decorator

class ColorTestResult(unittest.runner.TextTestResult):
    def __init__(self, stream, descriptions, verbosity, config, filter_categories):
        super().__init__(stream, descriptions, verbosity)
        self.config = config
        self.quiet = config['output']['quiet']
        self.use_colors = not config['output']['no_color']
        self.show_docstrings = config['output']['show_docstrings']
        self.slow_threshold = config['timing']['slow_test_threshold']
        self.tests_by_class = defaultdict(list)
        self.test_times = {}
        self.test_docs = {}
        self.filter_categories = filter_categories
        self.test_categories: dict[str, Set[str]] = {}
        self._started_at = None

        # Configure logging based on config
        logging.basicConfig(
            level=getattr(logging, config['logging']['level']),
            format=config['logging']['format']
        )

    def colored(self, text, color):
        if self.use_colors:
            return f"{color}{text}{Style.RESET_ALL}"
        return text

    def startTest(self, test):
        self._started_at = time.time()
        test_name = test._testMethodName
        test_class = test.__class__.__name__
        
        # Get test categories
        test_method = getattr(test, test_name)
        categories = getattr(test_method, 'test_categories', set())
        
        # Skip test if it doesn't match the filter
        if self.filter_categories and not (self.filter_categories & categories):
            self.stream.writeln(f"Skipped {test_name} (category filter)")
            return
            
        if test_class not in self.tests_by_class:
            self.tests_by_class[test_class] = []
            
        # Store the test's docstring
        doc = test_method.__doc__ or "No description provided"
        self.test_docs[f"{test_class}.{test_name}"] = doc
        
        self.test_categories[f"{test_class}.{test_name}"] = categories
        
        super().startTest(test)
        self.tests_by_class[test_class].append((test_name, True))

    def stopTest(self, test):
        elapsed = time.time() - self._started_at
        self.test_times[f"{test.__class__.__name__}.{test._testMethodName}"] = elapsed
        if self.config['timing']['warn_on_slow'] and elapsed > self.slow_threshold:
            self.stream.write(f" {self.colored(f'({elapsed:.2f}s ⚠)', Fore.YELLOW)}")
        else:
            self.stream.write(f" {self.colored(f'({elapsed:.2f}s)', Fore.BLUE)}")
        self.stream.flush()

    def addSuccess(self, test):
        self.stream.write(f"{self.colored('✓', Fore.GREEN)} ")
        self.stream.flush()
        super().addSuccess(test)

    def addError(self, test, err):
        self.stream.write(f"{self.colored('E', Fore.RED)} ")
        self.stream.flush()
        super().addError(test, err)
        self._mark_test_failed(test)

    def addFailure(self, test, err):
        self.stream.write(f"{self.colored('F', Fore.RED)} ")
        self.stream.flush()
        super().addFailure(test, err)
        self._mark_test_failed(test)

    def _mark_test_failed(self, test):
        class_name = test.__class__.__name__
        test_name = test._testMethodName
        for i, (name, _) in enumerate(self.tests_by_class[class_name]):
            if name == test_name:
                self.tests_by_class[class_name][i] = (name, False)
                break

    def _print_categories_summary(self):
        # Collect all unique categories
        all_categories = set()
        for cats in self.test_categories.values():
            all_categories.update(cats)

        if all_categories:
            self.stream.writeln("\n=== Categories ===")
            for category in sorted(all_categories):
                tests = [test for test, cats in self.test_categories.items() if category in cats]
                self.stream.writeln(f"\n{category} ({len(tests)} tests):")
                for test in sorted(tests):
                    self.stream.writeln(f"  - {test}")

class ColorTestRunner(unittest.TextTestRunner):
    def __init__(self, **kwargs):
        self.config = kwargs.pop('config', load_config())
        self.filter_categories = kwargs.pop('filter_categories', set())
        super().__init__(**kwargs)

    def _makeResult(self):
        return ColorTestResult(
            self.stream,
            self.descriptions,
            self.verbosity,
            config=self.config,
            filter_categories=self.filter_categories
        )

    def run(self, test):
        result = super().run(test)
        self._print_summary(result)
        return result

    def _print_summary(self, result):
        use_colors = not self.config['output']['no_color']
        self.stream.writeln(f"\n{Fore.CYAN if use_colors else ''}=== Test Summary ==={Style.RESET_ALL if use_colors else ''}")
        self.stream.writeln(f"\nTotal Tests: {result.testsRun}")
        
        # Calculate passed tests (can't be negative)
        passed = max(0, result.testsRun - len(result.failures) - len(result.errors))
        self.stream.writeln(f"Passed: {Fore.GREEN if use_colors else ''}{passed}{Style.RESET_ALL if use_colors else ''}")
        
        if result.failures:
            self.stream.writeln(f"Failed: {Fore.RED if use_colors else ''}{len(result.failures)}{Style.RESET_ALL if use_colors else ''}")
        if result.errors:
            self.stream.writeln(f"Errors: {Fore.RED if use_colors else ''}{len(result.errors)}{Style.RESET_ALL if use_colors else ''}")

        self.stream.writeln(f"\n{Fore.CYAN if use_colors else ''}=== Test Breakdown ==={Style.RESET_ALL if use_colors else ''}")
        
        # Print test breakdown
        for class_name, tests in sorted(result.tests_by_class.items()):
            total_class_time = sum(result.test_times.get(f"{class_name}.{test_name}", 0) 
                                 for test_name, _ in tests)
            self.stream.writeln(f"\n{Fore.YELLOW if use_colors else ''}{class_name}{Style.RESET_ALL if use_colors else ''} ({total_class_time:.2f}s total):")
            
            for test_name, passed in sorted(tests):
                status = f"{Fore.GREEN if use_colors else ''}✓{Style.RESET_ALL if use_colors else ''}" if passed else f"{Fore.RED if use_colors else ''}✗{Style.RESET_ALL if use_colors else ''}"
                time_taken = result.test_times.get(f"{class_name}.{test_name}", 0)
                time_color = Fore.YELLOW if time_taken > self.config['timing']['slow_test_threshold'] else Fore.BLUE
                
                if self.config['output']['show_docstrings']:
                    doc = result.test_docs.get(f"{class_name}.{test_name}", "").split('\n')[0]
                    self.stream.writeln(f"  {status} {test_name} {time_color if use_colors else ''}({time_taken:.2f}s){Style.RESET_ALL if use_colors else ''}")
                    if doc:
                        self.stream.writeln(f"    {doc}")

        # Print categories summary
        if hasattr(result, 'test_categories') and result.test_categories:
            self.stream.writeln(f"\n{Fore.CYAN if use_colors else ''}=== Categories ==={Style.RESET_ALL if use_colors else ''}")
            all_categories = set()
            for cats in result.test_categories.values():
                all_categories.update(cats)

            for category in sorted(all_categories):
                tests = [test for test, cats in result.test_categories.items() if category in cats]
                self.stream.writeln(f"\n{Fore.YELLOW if use_colors else ''}{category}{Style.RESET_ALL if use_colors else ''} ({len(tests)} tests):")
                for test in sorted(tests):
                    self.stream.writeln(f"  - {test}")

def run_tests():
    config = load_config()
    args = parse_args(config)
    
    # Override config with command line arguments
    config['output']['quiet'] = args.quiet
    config['output']['verbose'] = args.verbose
    config['output']['no_color'] = args.no_color

    # Load custom config if specified
    if args.config:
        with open(args.config) as f:
            config.update(yaml.safe_load(f))
    
    filter_categories = set(args.category) if args.category else set()
    
    runner = ColorTestRunner(
        verbosity=2,
        config=config,
        filter_categories=filter_categories
    )
    
    loader = unittest.TestLoader()
    suite = loader.discover('tests', pattern=config['patterns']['test_files'])
    runner.run(suite)

if __name__ == '__main__':
    run_tests() 