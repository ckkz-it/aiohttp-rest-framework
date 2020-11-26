from pathlib import Path

from setuptools import find_packages, setup

from aiohttp_rest_framework import __version__

with open(Path(__file__).parent / "README.md") as f:
    long_description = f.read()

setup(
    name="aiohttp_rest_framework",
    version=__version__,
    url="https://github.com/ckkz-it/aiohttp-rest-framework",
    license="MIT",
    author="Andrey Laguta",
    author_email="cirkus.kz@gmail.com",
    description="Rest framework for aiohttp web server",
    long_description=long_description,
    long_description_content_type="text/markdown",
    keywords=("restframework rest_framework aiohttp"
              " serializers asyncio rest aiohttp_rest_framework"),
    packages=find_packages(exclude=("tests", "tests.*")),
    python_requires=">=3.6",
    install_requires=[
        "aiohttp",
        "marshmallow",
        "SQLAlchemy==1.4.0b1",
        "psycopg2",
        "asyncpg",
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Web Environment",
        "Framework :: AsyncIO",
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Topic :: Internet :: WWW/HTTP",
        "License :: OSI Approved :: MIT License",
    ]
)
