<html><head>
    <title>chill-filter sample screening - User Guide</title>
    {% include "_header.html" %}
</head>

  <body>
    <main class="container">
      {% filter markdownify %}
# The chill-filter user guide

chill-filter is a rapid sample-screening Web application that comprehensively
determines the composition of a shotgun sequence data set. It should take
about 10 seconds to process an uploaded sample.

You could use it to:

* detect microbial contaminants in a eukaryotic genome sequencing project (e.g. [Bu5](/example?filename=Bu5.abund.k51.s100_000.sig.zip));
* detect host contamination in a microbiome sequencing project (e.g. [SRR5650070](/example?filename=SRR5650070.k51.s100_000.sig.zip));
* figure out what's in an unknown or problematic sample (e.g. [ERR2245457](/example?filename=ERR2245457.k51.s100_000.sig.zip));

chill-filter will sensitively detect the presence of large genomes
(500kb and up) at sequencing depths as low as 0.1x.

The main value of chill-filter is that it is fast, sensitive, and
comprehensive. If you want a full taxonomic breakdown of your sample,
there are other tools you might use,
e.g. [sourmash](https://sourmash.readthedocs.io/), but they don't run in
a Web browser :).

## How do you use chill-filter?

On the [front page](/), select a FASTA or FASTQ file to upload. The
file can be in a compressed (gzip or bzip2) format, and can be either
raw sequencing data (e.g. Illumina, PacBio, or Nanopore) or an
assembly. No prior filtering or processing of the data is required, and
we don't recommend doing any, since it may affect interpretation of the
results.

This file will be processed and compressed locally, in your browser,
and then uploaded to the chill-filter Web site. Most data sets will compress
to under 1 MB.

After a brief delay (hopefully under 10 seconds!) you should see a report
of what chill-filter has detected in your data!

If given reads, chill-filter will estimate the abundances of the
detected genomes in the read data set, as well as the total amount of
sequence (in reads) that should map. See [the Bu5 read data set](/example?filename=Bu5.abund.k51.s100_000.sig.zip) for an example.

If given an assembly, chill-filter will estimate the total number of bases
that should align between the assembly and the detected genomes. See [the Bu5 assembly data set]() for an example.

chill-filter estimates are generally a significant _underestimate_ of
mapping rates and abundances. This is largely a result of differences
between what is being sequenced and what is in the database; chill-filter
cannot detect or account for these differences.

## What does chill-filter look for?

As of Dec 2024, chill-filter matches against the human genome, 8
individual animal genomes (cow, dog, horse, cat, chicken, mouse, goat,
and pig), and two combined databases - GenBank plants and
[GTDB R220](https://gtdb.ecogenomic.org/stats/r220) microbes. These
last two databases are merged, so you can only detect that there is a
match, without seeing what the matching genomes are.

GenBank plants contains approximately 1700 plant genomes (all plant genomes
as of Dec 2024). GTDB RS220 contains approximately 584,000 bacterial genomes
and 12,500 archaeal genomes.

## Questions, comments, or requests?

Please visit the [Frequently Asked Questions](/faq) page, or ask a
question in
[the issue tracker](https://github.com/dib-lab/chill-filter/issues)!
You can also e-mail us at [chill@sourmash.bio](mailto:chill@sourmash.bio).

## Who is responsible for chill-filter?

chill-filter is a product of
[the sourmash project](https://github.com/sourmash-bio/).

      {% endfilter %}
{% include "_footer.html" %}
    </main>
   </body>
</html>
