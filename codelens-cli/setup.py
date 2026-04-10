from setuptools import setup, find_packages

setup(
    name="codelens",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "anthropic>=0.30.0",
        "click>=8.1.0",
        "pyyaml>=6.0",
        "python-dotenv>=1.0.0",
    ],
    extras_require={
        "dev": ["pytest", "pytest-cov", "black", "flake8", "isort"],
    },
    entry_points={
        "console_scripts": [
            "codelens=codelens.cli:main",
        ],
    },
    python_requires=">=3.9",
)
