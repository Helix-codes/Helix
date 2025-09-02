from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="helix-sdk",
    version="0.1.0",
    author="Helix Team",
    author_email="dev@helix.storage",
    description="Python SDK for Helix permanent encrypted storage on Solana + Arweave",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Helix-codes/helix-sdk-python",
    project_urls={
        "Bug Tracker": "https://github.com/Helix-codes/helix-sdk-python/issues",
        "Documentation": "https://helix.storage/docs",
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Security :: Cryptography",
    ],
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "httpx>=0.25.0",
        "solana>=0.30.0",
        "solders>=0.18.0",
        "cryptography>=41.0.0",
        "pynacl>=1.5.0",
        "aiofiles>=23.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "mypy>=1.0.0",
            "black>=23.0.0",
            "ruff>=0.1.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "helix=helix_sdk.cli:main",
        ],
    },
)
