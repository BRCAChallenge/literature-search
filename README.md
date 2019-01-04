# pubMunch-BRCA

Literature search pipeline for [BRCA Exchange](https://brcaexchange.org/)

# Overview

Attempts to download all [PubMed](https://en.wikipedia.org/wiki/PubMed) papers with BRCA in the title or abstract and then look for variants mentioned in the text and supplemental material. Download and variant search courtesy of [pubMunch](https://github.com/maximilianh/pubMunch) followed by normalization to HGVS courtesy of [Biocommons HVGS](https://github.com/biocommons/hgvs) and export into a literature.json for ingest into BRCA Exchange.

# Manual Operation

Build a local docker that includes this crawler and pubMunch
```
make build
```

Start up the docker and within it get all the refernces
```
make debug
make references
```

In a separate terminal run a local [Biocommons Universal Transcript Archive](https://github.com/biocommons/uta) server
```
make uta
```

And finally crawl from within the crawler docker crawl
```
make crawl
```

Successive runs of crawl will just download new papers. Exporting to literature.json is currently via the export.ipynb notebook.
