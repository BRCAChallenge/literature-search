# literature-search

Literature search pipeline for [BRCA Exchange](https://brcaexchange.org/)

# Overview

Attempts to download all [PubMed](https://en.wikipedia.org/wiki/PubMed) papers with BRCA in the title or abstract and then look for variants mentioned in the text and supplemental material. Download and variant search courtesy of [pubMunch](https://github.com/maximilianh/pubMunch) followed by normalization to HGVS courtesy of [Biocommons HVGS](https://github.com/biocommons/hgvs) and export into a literature.json file for ingest into BRCA Exchange.

# Running

Make a local copy of pubConfExample and fill in your email and keys.

Create a local references directory where the static reference files will be stored.

Create a local crawl directory where the downloaded papers and output will be stored.

Download references (only need to run once):
```
docker run --rm -it \
  --user=`id -u`:`id -g` \
  -v path/to/your/pubConf:/.pubConf:ro \
  -v path/to/references/storage:/references \
  -v path/to/crawl/storage:/crawl \
	brcachallenge/literature-search:latest references
```

Download a single paper as a test:
```
docker run --rm -it \
  --user=`id -u`:`id -g` \
  -v path/to/your/pubConf:/.pubConf:ro \
  -v path/to/references/storage:/references \
  -v path/to/crawl/storage:/crawl \
	brcachallenge/literature-search:latest --pmid 9042909 crawl
```

You should find a literature.json file under the crawl directory with a list of the papers crawled, their abstract and then any variants found along with snippets around the mention of the variant. Remove the --pmid to crawl all papers. See run.py for additional sub-commands to just download, convert, find and export.

```
{
  "date": "2019-04-23T16:27:27", 
  "papers": {
    "9042909": {
      "abstract": "The mutations 185delAG....", 
      "articleId": 5009042909,
    }
  }, 
  "variants": {
    "chr13:g.32340300:GT>G": [
      {
        "mentions": [
          "1997). In the Ashkenazi Jewish population, three founder mutations, 185delAG and 5382insC in the BRCA1 gene  921 and<<< 6174delT>>> in the ..",
          ...
        ],
        "pmid": "9042909", 
        "points": 3
      }
      ...
    ],
    "chr13:g.32340526:AT>A":
    ...
  }
}
```
You can run each individual step of the crawler as well:

```
docker run brcachallenge/literature-search:latest
Usage: run.py [OPTIONS] COMMAND [ARGS]...

Options:
  --debug / --no-debug  Generate debug output
  --pmid TEXT           PMID to crawl
  --help                Show this message and exit.

Commands:
  convert     Convert papers to text
  crawl       Crawl latest papers...
  download    Download papers
  export      Export literature.json
  find        Find variants in all papers text
  lovd        Run LOVD test
  match       Match variants to papers
  references  Download references
  update      Update list of variants and pubmed ids
```

# Developing and Debugging

Build a local docker that includes this crawler and pubMunch
```
make build
```

Start the docker, map the local code into /app and launch bash:
```
make debug
```

Download the references:
```
python3 run.py references
```

Crawl from within docker a single paper
```
python3 run.py --pmid 9042909 crawl
```
