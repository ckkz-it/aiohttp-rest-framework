FROM python:3.9-slim-buster

ENV PYTHONUNBUFFERED 1

ARG UID=1000
ARG GID=1000
RUN groupadd --force --gid $GID appgroup \
    && useradd --uid $UID --gid appgroup --shell /bin/bash --create-home appuser

RUN apt-get update && apt-get install --no-install-recommends --assume-yes \
        git \
        bash \
        libpq-dev \
        g++ \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /usr/src/app \
    && mkdir -p /tests

COPY requirements.txt /usr/src/app/requirements.txt

RUN python3 -m pip install --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r /usr/src/app/requirements.txt

ENV PYTHONPATH="/usr/src/app:/tests:${PATH}"

COPY . /usr/src/app

RUN chown -R appuser:appgroup /usr/src/app
USER appuser
WORKDIR /usr/src/app
