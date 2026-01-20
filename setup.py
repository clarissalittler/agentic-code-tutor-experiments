#!/usr/bin/env python3
"""Setup script for compatibility with older pip versions.

Modern pip reads from pyproject.toml, but older versions need this file.
"""
from setuptools import setup, find_packages

setup(
    name="code-tutor",
    version="0.1.0",
    description="An intelligent, respectful code review and tutoring CLI tool",
    author="Code Tutor Contributors",
    license="MIT",
    python_requires=">=3.9",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "click>=8.1.0",
        "anthropic>=0.18.0",
        "rich>=13.0.0",
    ],
    entry_points={
        "console_scripts": [
            "code-tutor=code_tutor.cli:main",
        ],
    },
)
