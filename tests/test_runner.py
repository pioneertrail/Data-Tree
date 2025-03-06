import unittest
import sys
from collections import defaultdict
from colorama import init, Fore, Style

# Initialize colorama for Windows support
init()

class ColorTestResult(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tests_by_class = defaultdict(list)

    def startTest(self, test):
        super().startTest(test)
        class_name = test.__class__.__name__
        test_name = test._testMethodName
        self.tests_by_class[class_name].append((test_name, True))  # True = passed by default

    def addError(self, test, err):
        self.stream.write(f'{Fore.RED}E{Style.RESET_ALL} ')
        super().addError(test, err)
        self._mark_test_failed(test)

    def addFailure(self, test, err):
        self.stream.write(f'{Fore.RED}F{Style.RESET_ALL} ')
        super().addFailure(test, err)
        self._mark_test_failed(test)

    def addSuccess(self, test):
        self.stream.write(f'{Fore.GREEN}✓{Style.RESET_ALL} ')
        super().addSuccess(test)

    def _mark_test_failed(self, test):
        class_name = test.__class__.__name__
        test_name = test._testMethodName
        # Find and mark the test as failed
        for i, (name, _) in enumerate(self.tests_by_class[class_name]):
            if name == test_name:
                self.tests_by_class[class_name][i] = (name, False)
                break

class ColorTestRunner(unittest.TextTestRunner):
    def __init__(self, *args, **kwargs):
        kwargs['resultclass'] = ColorTestResult
        super().__init__(*args, **kwargs)

    def run(self, test):
        result = super().run(test)
        self._print_summary(result)
        return result

    def _print_summary(self, result):
        print(f"\n{Fore.CYAN}=== Test Summary ==={Style.RESET_ALL}")
        print(f"\nTotal Tests: {result.testsRun}")
        passed = result.testsRun - len(result.failures) - len(result.errors)
        print(f"Passed: {Fore.GREEN}{passed}{Style.RESET_ALL}")
        if result.failures:
            print(f"Failed: {Fore.RED}{len(result.failures)}{Style.RESET_ALL}")
        if result.errors:
            print(f"Errors: {Fore.RED}{len(result.errors)}{Style.RESET_ALL}")

        print(f"\n{Fore.CYAN}=== Test Breakdown ==={Style.RESET_ALL}")
        for class_name, tests in sorted(result.tests_by_class.items()):
            print(f"\n{Fore.YELLOW}{class_name}:{Style.RESET_ALL}")
            for test_name, passed in sorted(tests):
                status = f"{Fore.GREEN}✓{Style.RESET_ALL}" if passed else f"{Fore.RED}✗{Style.RESET_ALL}"
                print(f"  {status} {test_name}")

def run_tests():
    loader = unittest.TestLoader()
    suite = loader.discover('tests')
    runner = ColorTestRunner(verbosity=2)
    runner.run(suite)

if __name__ == '__main__':
    run_tests() 