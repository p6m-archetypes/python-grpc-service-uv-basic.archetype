#!/bin/sh

# Clean and remove version control directories if they exist
if [ -d "contents/base/prefix-name-suffix-name" ]; then

	pushd contents/base/prefix-name-suffix-name
	rm -rf __pycache__
	rm -rf dist
	rm -rf .venv
	rm CLAUDE.*
	uv clean
	rm -rf .jj
	rm -rf .git
	popd

	templatize escape contents/base/
fi

# Case Shapes
templatize shapes "org-name" "{{ org-name }}" -p -c contents/base/
templatize shapes "solution-name" "{{ solution-name }}" -p -c contents/base/
templatize shapes "prefix-name" "{{ prefix-name }}" -p -c contents/base/
templatize shapes "suffix-name" "{{ suffix-name }}" -p -c contents/base/

# Titles
templatize exact "Org Name" "{{ org-title }}" -p -c contents/base
templatize exact "Solution Name" "{{ solution-title }}" -p -c contents/base
templatize exact "Prefix Name" "{{ prefix-title }}" -p -c contents/base
templatize exact "Suffix Name" "{{ suffix-title }}" -p -c contents/base
