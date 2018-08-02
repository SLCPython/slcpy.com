#!/bin/sh
#
# Simple test to check if the codebase is pep8 compliant

flake8 --exclude 'migrations,alembic' slcpy
