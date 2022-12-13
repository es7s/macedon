## *PROJECT_NAME             ## *PROJECT_DESCRIPTION
## (C) *CYR                  ## A. Shavykin <0.delameter@gmail.com>
##---------------------------##-------------------------------------------------------------
.ONESHELL:
.PHONY: help test docs

PROJECT_NAME = *PROJECT_NAME
PROJECT_NAME_PUBLIC = ${PROJECT_NAME}
PROJECT_NAME_PRIVATE = ${PROJECT_NAME}-test

HOST_DEFAULT_PYTHON ?= /usr/bin/python
VENV_DEV_PATH = venv

DOTENV = .env
DOTENV_DIST = .env.dist
OUT_BUILD_RELEASE_PATH = dist
OUT_BUILD_DEV_PATH = dist-dev
OUT_DEPS_PATH = misc/depends
OUT_COVER_PATH = misc/coverage

include ${DOTENV_DIST}
-include ${DOTENV}
export
VERSION ?= 0.0.0

NOW    := $(shell date '+%Y-%b-%0e.%H%M%S.%3N')
BOLD   := $(shell tput -Txterm bold)
GREEN  := $(shell tput -Txterm setaf 2)
YELLOW := $(shell tput -Txterm setaf 3)
BLUE   := $(shell tput -Txterm setaf 4)
DIM    := $(shell tput -Txterm dim)
RESET  := $(shell printf '\e[m')
                                # tput -Txterm sgr0 returns SGR-0 with
                                # nF code switching esq, which displaces the columns
## Common commands

help:   ## Show this help
	@fgrep -h "##" $(MAKEFILE_LIST) | fgrep -v @fgrep | sed -Ee 's/^(##)\s?(\s*#?[^#]+)#*\s*(.*)/\1${YELLOW}\2${RESET}#\3/; s/(.+):(#|\s)+(.+)/##   ${GREEN}\1${RESET}#\3/; s/\*(\w+)\*/${BOLD}\1${RESET}/g; 2~1s/<([*<@>.A-Za-z0-9_-]+)>/${DIM}\1${RESET}/gi' -e 's/(\x1b\[)33m#/\136m/' | column -ts# | sed -Ee 's/ {3}>/ >/'

environment:  ## Show environment vars used by this Makefile
	@echo HOST_DEFAULT_PYTHON=${HOST_DEFAULT_PYTHON}
	echo OUT_BUILD_DEV_PATH=${PWD}/${OUT_BUILD_DEV_PATH}
	echo OUT_BUILD_RELEASE_PATH=${PWD}/${OUT_BUILD_RELEASE_PATH}
	echo OUT_COVER_PATH=${PWD}/${OUT_COVER_PATH}
	echo OUT_DEPS_PATH=${PWD}/${OUT_DEPS_PATH}
	echo PIPX_DEFAULT_PYTHON=${PIPX_DEFAULT_PYTHON}
	echo VENV_DEV_PATH=${PWD}/${VENV_DEV_PATH}

reinit-build:  ## > Prepare environment for module building  <venv>
	rm -vrf ${VENV_DEV_PATH}
	if [ ! -f .env.build ] ; then cp -u ${DOTENV_DIST} ${DOTENV} && sed -i -Ee '/^VERSION=/d' ${DOTENV} ; fi
	${HOST_DEFAULT_PYTHON} -m venv ${VENV_DEV_PATH}
	${HOST_DEFAULT_PYTHON} -m pip install pipx
	${VENV_DEV_PATH}/bin/pip install -r requirements.txt -r requirements-dev.txt
	# ${VENV_DEV_PATH}/bin/python -m ${PROJECT_NAME} --version

all:   ## Prepare, run tests, generate docs and reports, build module
all: reinit-build test coverage build

##
## Pre-build

demolish-build:  ## Delete build output folders
	rm -f -v ${OUT_BUILD_RELEASE_PATH}/* ${PROJECT_NAME_PUBLIC}.egg-info/* ${PROJECT_NAME_PRIVATE}.egg-info/*

show-version: ## Show current package version
	@echo "Current version: ${YELLOW}${VERSION}${RESET}"

set-version: ## Set new package version
set-version: show-version
	@read -p "New version (press enter to keep current): " VERSION
	if [ -z $$VERSION ] ; then echo "No changes" && return 0 ; fi
	sed -E -i "s/^VERSION.+/VERSION=$$VERSION/" ${DOTENV_DIST}
	sed -E -i "s/^version.+/version = $$VERSION/" setup.cfg
	sed -E -i "s/^__version__.+/__version__ = \"$$VERSION\"/" ${PROJECT_NAME}/_version.py
	echo "Updated version: ${GREEN}$$VERSION${RESET}"

depends:  ## Build and display module dependency graph
	rm -vrf ${OUT_DEPS_PATH}
	mkdir -p ${OUT_DEPS_PATH}
	./pydeps.sh ${VENV_DEV_PATH}/bin/pydeps ${PROJECT_NAME} ${OUT_DEPS_PATH}

purge-cache:  ## Clean up pycache
	find . -type d \( -name __pycache__ -or -name .pytest_cache \) -print -exec rm -rf {} +

##
## Testing

test: ## Run pytest
	${VENV_DEV_PATH}/bin/pytest tests

test-verbose: ## Run pytest with detailed output
	${VENV_DEV_PATH}/bin/pytest tests -v

test-debug: ## Run pytest with VERY detailed output
	${VENV_DEV_PATH}/bin/pytest tests -v --log-file-level=DEBUG --log-file=logs/testrun.${NOW}.log
	if command -v bat &>/dev/null ; then bat logs/testrun.${NOW}.log -n --wrap=never ; else less logs/testrun.${NOW}.log ; fi

coverage: ## Run coverage and make a report
	rm -vrf ${OUT_COVER_PATH}
	${VENV_DEV_PATH}/bin/python -m coverage run tests -vv
	${VENV_DEV_PATH}/bin/coverage report
	${VENV_DEV_PATH}/bin/coverage html
	if [ -n $$DISPLAY ] ; then xdg-open ${OUT_COVER_PATH}/index.html ; fi

##
## Building / Packaging
###  local

reinstall-local:  ## > (Re)install as editable, inject latest deps  <pipx>
	@pipx uninstall ${PROJECT_NAME}
	pipx install ${PROJECT_NAME} --pip-args="-e ."
	# ${PROJECT_NAME} --version

###  dev

build-dev: ## Create new private build  <*-test>
build-dev: demolish-build
	sed -E -i "s/^name.+/name = ${PROJECT_NAME_PRIVATE}/" setup.cfg
	${VENV_DEV_PATH}/bin/python -m build --outdir ${OUT_BUILD_DEV_PATH}
	sed -E -i "s/^name.+/name = ${PROJECT_NAME_PUBLIC}/" setup.cfg

upload-dev: ## Upload last private build (=> dev registry)
	${VENV_DEV_PATH}/bin/twine \
	    upload \
	    --repository testpypi \
	    -u ${PYPI_USERNAME} \
	    -p ${PYPI_PASSWORD_DEV} \
	    --verbose \
	    ${OUT_BUILD_DEV_PATH}/*

install-dev: ## Install latest private build from dev registry
	pipx uninstall ${PROJECT_NAME_PRIVATE}
	pipx install ${PROJECT_NAME_PRIVATE}==${VERSION} --pip-args="-i https://test.pypi.org/simple/"

### release

build: ## Create new *public* build
build: demolish-build
	${VENV_DEV_PATH}/bin/python -m build

upload: ## Upload last *public* build (=> PRIMARY registry)
	${VENV_DEV_PATH}/bin/twine \
	    upload \
	    -u ${PYPI_USERNAME} \
	    -p ${PYPI_PASSWORD} \
	    --verbose \
	    ${OUT_BUILD_RELEASE_PATH}/*

install: ## > Install latest *public* build from PRIMARY registry
	pipx install ${PROJECT_NAME_PUBLIC}

##
