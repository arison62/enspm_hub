#!/bin/bash

set -o errexit
set -o nounset

pip install -r requirements.txt
npm install
npm run build
python manage.py migrate --noinput
python manage.py collectstatic --noinput
python manage.py populate_references --table=all
python manage.py createsuperuser --noinput
