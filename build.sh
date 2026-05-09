#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --noinput
python manage.py migrate

# Optional: Seed data if you want it to happen on every deploy
# python manage.py seed_data
