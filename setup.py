from setuptools import setup, find_packages

setup(
    name="ai_search",
    version="0.2.0",
    description="AI-powered search system using Google Custom Search and AI processing",
    author="OndrejDuda022",
    python_requires=">=3.8",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "google-api-python-client>=2.0.0",
        "python-dotenv>=0.19.0",
        "pydantic>=2.0.0",
        "requests>=2.25.0",
        "beautifulsoup4>=4.9.0",
        "selenium>=4.0.0",
        "webdriver-manager>=3.5.0",
        "pdfplumber>=0.5.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=3.0.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "ai-search=main:main",
        ]
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
    ],
)