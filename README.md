# chill-filter:Rapid sample screening for shotgun sequencing data

## Quickstart for the Web server:

0. Clone the repo:

```
git clone https://github.com/dib-lab/chill-filter
cd chill-filter/
```

1. Install flask, sourmash_plugin_branchwater, pandas, and snakemake.

```
conda env create -f environment.yml -n chill
conda activate chill
```

2. Download the databases from [the Open Science Framework project](https://osf.io/m85ux/), and unpack them into `prepare-db/outputs/`.

```
curl -JLO https://osf.io/download/pwfn8/
mkdir -p prepare-db/outputs/
unzip -d prepare-db/outputs/ -nu chill-filter-db-0.1.zip
```

3. Run snakemake in the `sample-db/` directory to index the databases. It should take a few minutes at most.

```
(cd prepare-db && snakemake -j 1 -p)
```

4. Run `chill_filter_web`:

```
mkdir -p /tmp/chill
python -m chill_filter_web
```

This will start a server at http://localhost:5000/, by default.

5. Try uploading k=51, scaled=100_000 sketches!

e.g. there are a bunch in `examples/` to try.
