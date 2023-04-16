#!/bin/sh

export PYTHONPATH=".:$PYTHONPATH"
export DJANGO_SETTINGS_MODULE="test_settings"

PROG="$0"
CMD="$1"
shift

usage() {
    echo "USAGE: $PROG [command]"
    echo "  test - run the ratelimit tests"
    echo "  lint - run flake8 (alias: flake8)"
    echo "  shell - open the Django shell"
    echo "  build - build a package for release"
    echo "  check - run twine check on build artifacts"
    exit 1
}

case "$CMD" in
    "test" )
        echo "Django version: $(python -m django --version)"
        python \
            -W error::ResourceWarning \
            -W error::DeprecationWarning \
            -W error::PendingDeprecationWarning \
            -m django \
            test \
            django_ratelimit \
            "$@"
        ;;
    "lint"|"flake8" )
        echo "Flake8 version: $(flake8 --version)"
        flake8 "$@" django_ratelimit/
        ;;
    "shell" )
        python -m django shell
        ;;
    "build" )
        rm -rf dist/*
        python -m build
        ;;
    "check" )
        twine check dist/*
        ;;
    * )
        usage ;;
esac
