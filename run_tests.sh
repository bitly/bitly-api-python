#!/bin/bash

if [ "$TRAVIS_SECURE_ENV_VARS" = "true" ]; then
    export BITLY_ACCESS_TOKEN="$SECURE_ACCESS_TOKEN"
fi

if [ -n "$BITLY_ACCESS_TOKEN" ]; then
    nosetests
fi
