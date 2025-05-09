
SUPER_LINTER_CONFIGS = \
  .eslintrc.json \
  .htmlhintrc \
  .jscpd.json \
  .ruby-lint.yml \
  .stylelintrc.json

.PHONY: all

all: clean push test coverage lint format upload super-lint

SHELL := /bin/bash
CWD := $(shell dirname $(realpath $(firstword $(MAKEFILE_LIST))))

clean: 
	- rm -rvf dist
	- find . -type d -name "jira_creator.egg-info" -exec rm -rf {} +
	- find . -type d -name "__pycache__" -exec rm -r {} +
	- find . -type f -name "*.pyc" -delete
	- find . -type f -name ".coverage*" -delete
	- find . -type f -name "coverage.xml" -delete
	- find . -type d -name ".pytest_cache" -exec rm -rf {} +
	- rm -rvf htmlcov
	- rm -rvf log.log
	- rm -rvf d_fake_seeder/log.log
	- rm -rvf .pytest_cache
	- rm -rvf debbuild
	- rm -rvf rpmbuild
	- rm -rvf *.deb
	- rm -rvf *.rpm
	- sudo rm -rvf .mypy_cache

push: clean
	git add -A
	git commit --amend --no-edit 
	git push -u origin main:main -f

upload: clean
	python3 -m pip install --upgrade build
	python3 -m pip install --upgrade twine
	python3 -m build
	python3 -m twine upload --repository pypi dist/*

super-lint: $(SUPER_LINTER_CONFIGS)
	docker run --rm \
	-e SUPER_LINTER_LINTER=error \
	-e LINTER_OUTPUT=error \
	-e LOG_LEVEL=ERROR \
	-e RUN_LOCAL=true \
	-e VALIDATE_PYTHON_MYPY=false \
	-e VALIDATE_JSCPD=false \
	-e FILTER_REGEX_EXCLUDE="(^|/)\.git(/|$)" \
	-e GIT_IGNORE=true \
	-v $$(pwd):/tmp/lint \
	-w /tmp/lint \
	github/super-linter:latest --quiet

# --- External Linter Configs ---
.eslintrc.json:
	curl -sSL -o $@ https://raw.githubusercontent.com/dmzoneill/dmzoneill/main/.github/linters/.eslintrc.json

.htmlhintrc:
	curl -sSL -o $@ https://raw.githubusercontent.com/dmzoneill/dmzoneill/main/.github/linters/.htmlhintrc

.jscpd.json:
	curl -sSL -o $@ https://raw.githubusercontent.com/dmzoneill/dmzoneill/main/.github/linters/.jscpd.json

.ruby-lint.yml:
	curl -sSL -o $@ https://raw.githubusercontent.com/dmzoneill/dmzoneill/main/.github/linters/.ruby-lint.yml

.stylelintrc.json:
	curl -sSL -o $@ https://raw.githubusercontent.com/dmzoneill/dmzoneill/main/.github/linters/.stylelintrc.json

test:
	pytest -v tests

coverage:
	pytest --cov=gnome_extension_publisher --cov-report=term-missing tests/

lint:
	black .
	isort .
	flake8 --max-line-length 120 .
	pylint gnome_extension_publisher tests

format:
	isort .
	black .