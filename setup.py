"""Setup configuration for AgentBender library."""

from setuptools import setup, find_packages
from pathlib import Path

# Read README if exists
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

setup(
    name="agentbender",
    version="1.0.0",
    description="Library for automatic generation of UI autotests using LLM",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Senior Python Developer / Lead Test Automation Engineer",
    author_email="",
    url="https://github.com/your-org/agentbender",
    packages=find_packages(exclude=["tests", "tests.*"]),
    python_requires=">=3.9",
    install_requires=[
        "playwright>=1.40.0",
        "pydantic>=2.0.0",
        "jinja2>=3.1.0",
        "pyyaml>=6.0",
        "httpx>=0.25.0",
        "ollama>=0.1.0",
        "black>=23.0.0",
        "autopep8>=2.0.0",
        "click>=8.1.0",
        "structlog>=23.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "agentbender=agentbender.cli.main:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Testing",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)

