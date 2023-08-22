#!/usr/bin/env bash
pip install virtualenv
virtualenv -p /usr/bin/python3.11 .env
source .env/bin/activate && pip install -r requirements-dev.txt