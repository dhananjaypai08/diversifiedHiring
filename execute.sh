#!/bin/bash

echo "Starting Your Project"
echo "Give a name for your project"
read NAME

DJANGO_SETTINGS_MODULE="diversifynow.core.settings"
DJANGO_WSGI_MODULE="diversifynow.core.wsgi"
echo "Config set"

activate() {
    "env/Scripts/activate"
}
echo "Virutal environment Activated"

cd $diversifynow
export DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS_MODULE
export PYTHONPATH=$DJANGODIR:$PYTHONPATH

pip install -r requirements.txt
echo "Requirements are installed" 

python3 diversifynow/manage.py runserver
