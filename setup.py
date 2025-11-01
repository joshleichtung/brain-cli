from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="brain-cli",
    version="0.1.0",
    author="Josh",
    description="Agent-agnostic research and automation hub for terminal-based workflows",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/joshleichtung/brain-cli",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.11",
    install_requires=[
        "anthropic>=0.34.0",
        "google-generativeai>=0.3.0",
        "click>=8.1.0",
        "rich>=13.0.0",
        "pyyaml>=6.0",
        "python-dotenv>=1.0.0",
    ],
    entry_points={
        "console_scripts": [
            "brain=brain.cli:main",
        ],
    },
)
