.PHONY: install run test clean reset

install:
	python -m pip install --user -e .

run:
	python -m supervisions

test:
	python -m unittest discover -s tests -v

clean:
	find . -type d -name "__pycache__" -prune -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -prune -exec rm -rf {} +
	find . -type d -name "*.egg-info" -prune -exec rm -rf {} +
	rm -rf build dist

reset: clean install test
