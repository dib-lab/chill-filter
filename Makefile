.PHONY: dist

dist:
	python -m build

black:
	python -m black chill_filter_web

test:
	pytest
