from setuptools import setup, find_packages

setup(
    name="ai_search",
    version="0.1",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "openai",
        "google-api-python-client",
        "python-dotenv"
    ],
    entry_points={
        "console_scripts": [
            "ai-search=main:main",
        ]
    },
)