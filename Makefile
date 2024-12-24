.PHONY: dist

dist:
	python -m build

black:
	python -m black chill_filter_web

dbzip:
	cd prepare-db && zip -r ../chill-filter-db.zip outputs/* \
	    downloads/gtdb-rs220-phylum.sig.zip \
	    downloads/genbank-plants-2024.07.k51.s100_000.sig.zip \
	    downloads/podar-ref.sig.zip

test:
	pytest
