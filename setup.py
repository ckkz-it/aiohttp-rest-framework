from setuptools import setup

from aiohttp_rest_framework import __version__

with open("README.md") as f:
    long_description = f.read()

setup(
    name="aiohttp_rest_framework",
    version=__version__,
    url="https://github.com/ckkz-it/aiohttp-rest-framework",
    license="MIT",
    author="Andrey Laguta",
    author_email="cirkus.kz@gmail.com",
    py_modules=["aiohttp_rest_framework"],
    description="Rest framework for aiohttp web server",
    long_description=long_description,
    long_description_content_type="text/markdown",
    keywords=("restframework rest_framework aiohttp"
              " serializers asyncio rest aiohttp_rest_framework"),
    packages=["aiohttp_rest_framework"],
    python_requires=">=3.6",
    install_requires=[
        "aiohttp",
        "aiohttp-cors",
        "aiopg",
        "marshmallow",
        "sqlalchemy",
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
        "Topic :: Internet :: WWW/HTTP",
        "License :: OSI Approved :: MIT License",
    ]
)
