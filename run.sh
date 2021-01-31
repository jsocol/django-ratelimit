#!/bin/bash

export PYTHONPATH=".:$PYTHONPATH"
export DJANGO_SETTINGS_MODULE="test_settings"

PROG="$0"
CMD="$1"
shift

usage() {
    echo "USAGE: $PROG [command]"
    echo "  test - run the ratelimit tests"
    echo "  flake8 - run flake8"
    echo "  shell - open the Django shell"
    exit 1
}

case "$CMD" in
    "test" )
        echo "Django version: $(python -m django --version)"
        python -m django test django_ratelimit "$@";;
    "flake8" )
        echo "Flake8 version: $(flake8 --version)"
        flake8 "$@" django_ratelimit/;;
    "shell" )
        python -m django shell ;;
    * )
        usage ;;
esac
