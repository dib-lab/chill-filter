# chill-filter: Rapid sample screening for shotgun sequencing data

## Quickstart for the Web site:

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
curl -JLO https://osf.io/download/5fw2v/
unzip -d prepare-db/ -nu chill-filter-db-0.4.zip
```

3. Run snakemake in the `sample-db/` directory to index the databases. It should take a few minutes at most.

```
(cd prepare-db && snakemake -j 1 -p)
```

4. Run `chill_filter_web`:

```
mkdir -p /tmp/chill
python -m chill_filter_web -p 5000
```

This will start a server at http://localhost:5000/

5. Try uploading some FASTQ or FASTA files, or check out the examples!
