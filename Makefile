.PHONY: install run web test clean reset demo

install:
	python -m pip install --user -e .

run:
	python -m supervisions

web:
	python -m supervisions.web

test:
	python -m unittest discover -s tests -v

clean:
	find . -type d -name "__pycache__" -prune -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -prune -exec rm -rf {} +
	find . -type d -name "*.egg-info" -prune -exec rm -rf {} +
	rm -rf build dist
	rm -f data/users.json
	rm -f data/supervision_requests.json

reset: clean install test

demo:
	@echo "[demo] admin creates user"
	python -m supervisions --role admin --username alice --create-user charlie --create-role regular
	@echo "[demo] regular user denied"
	@if python -m supervisions --role regular --username bob --create-user dave --create-role regular; then \
		echo "[demo] ERROR: regular user unexpectedly created a user"; \
		exit 1; \
	else \
		echo "[demo] OK: regular user was denied"; \
	fi
