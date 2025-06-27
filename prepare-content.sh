#!/bin/sh

rm -rf contents/base/* contents/base/.[^.]*
cp -r ../prefix-name-suffix-name contents/base/

pushd contents/base/prefix-name-suffix-name
rm -rf __pycache__
rm -rf .claude
rm -rf dist
rm -rf .venv
rm CLAUDE.*
uv clean
rm -rf .jj
rm -rf .git
popd
