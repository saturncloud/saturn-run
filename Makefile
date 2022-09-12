-include .env_deps .env_dev .env .env_local
export

SHELL=/bin/bash -O globstar
TEST_IMAGE_NAME ?= saturncloud/saturn-run:test
CONDA_ACTIVATE = source $$(conda info --base)/etc/profile.d/conda.sh ; conda activate ; conda activate
DATA_DIR ?= /data

.PHONY: format-backend
format-backend:
	@echo -e '\n\nCheck formatting with Black...'
	black --line-length 100 --exclude '/(\.vscode|node_modules)/' .
	isort saturn_run tests

.PHONY: check-unmerged-symbols
check-unmerged-symbols:
	# TODO: check for unmerged symbols such as >>>>>>
	@echo -e '\nCheck for "breakpoint()" or "import pdb" left on Python code'
	@! grep --color -nrE '(breakpoint\(\)|import pdb)' **/*.py

.PHONY: black
black:
	# If you make changes here, also edit .pre-commit-config.yaml to match
	#TODO: formatting discrepancies should raise errors instead of warnings
	@echo -e '\n\nCheck formatting with Black...'
	black  --line-length 100 --check --diff .

.PHONY: flake8
flake8:
	# If you make changes here, also edit .pre-commit-config.yaml to match
	@echo -e '\n\nFlake8 linting...'
	flake8 saturn_run
	flake8 tests

.PHONY: pylint
pylint:
	# pylint disables are handled in .pylintrc
	@echo -e '\n\npylint linting...'
	pylint saturn_run
	pylint tests/

.PHONY: mypy
mypy:
	mypy --config-file mypy.ini ./

.PHONY: isort
isort:
	isort saturn_run tests --check

.PHONY: bandit
bandit:
# runs bandit, excluding low-severity issues
	bandit -r saturn_run -ll

.PHONY: bandit-low
bandit-low:
# runs bandit, including low-severity issues
	bandit -r saturn_run

.PHONY: check-settings-variable-case
check-settings-variable-case:
	@ if grep -P '^(?!_)([a-z_]+) =' saturn_run/settings.py; then \
		echo "Found lowercase variable in settings.py - please use uppercase instead."; \
		exit 1; \
	fi

.PHONY: lint-backend
lint-backend: \
	check-unmerged-symbols \
	check-settings-variable-case \
	black \
	flake8 \
	pylint \
	mypy \
	isort



.PHONY: check-backend-test-markers
check-backend-test-markers:
	@echo "Checking for issues with test markers..." && \
	set -o pipefail && \
	TEST_MARKERS=$$(grep -R -E "mark\.gen_test" tests/ --exclude conftest.py | wc -l) && \
	echo "  * tests with @mark.gen_test: $${TEST_MARKERS}" && \
	TOTAL_TESTS=$$(grep -R -E "def test\_" tests/ --exclude conftest.py | wc -l) && \
	echo "  * total tests: $${TOTAL_TESTS}" && \
	if [ $${TEST_MARKERS} -ne $${TOTAL_TESTS} ]; then \
		echo "EROR: all tests in tests/ must be marked with @mark.gen_test"; \
		exit -1; \
	else \
		echo "No issues found with test markers"; \
	fi

.PHONY: test-backend
test-backend:
	pytest -n auto --cov-report term-missing --cov=saturn_run/ --cov-fail-under=60 -s

.PHONY: test-debug
test-debug:
	pytest -s tests

.PHONY: conda-update
conda-update:
	($(CONDA_ACTIVATE) base && (conda remove --all -n saturn_run -y || true) && mamba create -n saturn_run -y && $(CONDA_ACTIVATE) saturn_run)
	mamba env update -n saturn_run --file environment.yaml
