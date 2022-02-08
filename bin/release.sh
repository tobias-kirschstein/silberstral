#!/bin/sh

rm -r dist/*
python -m build
twine upload dist/*
# Username: tobias.kirschstein