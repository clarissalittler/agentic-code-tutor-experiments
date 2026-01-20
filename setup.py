#!/usr/bin/env python3
"""Minimal setup.py for compatibility with older pip versions.

All configuration is in pyproject.toml. This file is only needed for
pip versions < 21.3 that don't support PEP 517 builds by default.
"""
from setuptools import setup

setup()
