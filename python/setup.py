"""Setup configuration for YouTube Bulk Upload"""
from setuptools import setup, find_packages

setup(
    name="youtube-bulk-upload",
    version="1.0.0",
    description="Bulk upload videos from Google Drive to YouTube using metadata from Google Sheets",
    author="Oak National Academy",
    license="MIT",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.8",
    install_requires=[
        "google-auth>=2.25.0",
        "google-auth-oauthlib>=1.2.0",
        "google-auth-httplib2>=0.2.0",
        "google-api-python-client>=2.100.0",
        "python-dotenv>=1.0.0",
    ],
    extras_require={
        "dev": [
            "black>=24.0.0",
            "isort>=5.13.0",
            "mypy>=1.8.0",
            "pytest>=8.0.0",
            "pytest-watch>=4.2.0",
            "pytest-cov>=5.0.0",
            "pytest-mock>=3.12.0",
            "pytest-asyncio>=0.23.0",
            "ruff>=0.5.0",
            "types-requests>=2.31.0",
            "tqdm>=4.66.0",
            "rich>=13.7.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "youtube-bulk-upload=main:cli",
        ],
    },
)