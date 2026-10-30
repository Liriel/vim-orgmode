PLUGIN = orgmode
PREFIX = /usr/local
VIMDIR = $(PREFIX)/share/vim
PYTHON = python3
DOCDIR = ftplugin/orgmode/docs

all: build

build:

# install plugin at destination
install: doc indent ftdetect ftplugin syntax
	for i in doc indent ftdetect ftplugin syntax; do \
		find $$i -type f \( -name \*.txt -o -name \*.cnf -o -name \*.py -o -name \*.vim \) \
				-not -path '*/__pycache__/*' -not -path '$(DOCDIR)/*' | while read f; do \
			install -m 0755 -d $(DESTDIR)$(VIMDIR)/$$(dirname "$$f"); \
			install -m 0644 $$f $(DESTDIR)$(VIMDIR)/$$f; \
		done; \
	done

# remove generated files (caches, coverage data, built documentation)
clean:
	@find . \( -name .git -o -name .venv \) -prune -o -name __pycache__ -type d -prune -exec rm -rf {} +
	@rm -rf .pytest_cache .ruff_cache .coverage htmlcov $(DOCDIR)/_build

# run the unit tests and, if a Vim with +python3 is installed, the integration tests
test:
	$(PYTHON) -m pytest

# generate documentation
docs:
	$(PYTHON) -m sphinx -W --keep-going -b html $(DOCDIR) $(DOCDIR)/_build/html

# generate a test coverage report for all python files
coverage:
	$(PYTHON) -m coverage run -m pytest
	$(PYTHON) -m coverage report
	$(PYTHON) -m coverage html

# run the static code checker and check the formatting
lint:
	$(PYTHON) -m ruff check .
	$(PYTHON) -m ruff format --check .

# format the python code
format:
	$(PYTHON) -m ruff format .

.PHONY: all build test install clean docs coverage lint format
