#!/bin/bash

export PYTHONPATH=".:$PYTHONPATH"
export DJANGO_SETTINGS_MODULE="test_settings"

usage() {
    echo "USAGE: $0 [command]"
    echo "  test - run the ratelimit tests"
    echo "  flake8 - run flake8"
    echo "  shell - open the Django shell"
    exit 1
}

if command -v django-admin.py; then
    ENTRY=django-admin.py
else
    ENTRY=django-admin
fi


case "$1" in
    "test" )
        shift;
        echo "Django version: $($ENTRY --version)"
        $ENTRY test django_ratelimit "$@";;
    "flake8" )
        shift;
        echo "Flake8 version: $(flake8 --version)"
        flake8 "$@" django_ratelimit/;;
    "shell" )
        $ENTRY shell ;;
    * )
        usage ;;
esac
