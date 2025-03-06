from setuptools import setup, find_packages

setup(
    name="biographical-memory",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        'colorama>=0.4.6',
        'pyyaml>=6.0.1',
    ],
    python_requires='>=3.8',
) 