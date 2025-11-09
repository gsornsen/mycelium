"""Setup script for example Temporal application."""

from setuptools import find_packages, setup

setup(
    name="example-temporal-app",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "temporalio>=1.20.0",
        "pydantic>=2.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
        ],
    },
)
