# pubMunch-docker

This respository contains a docker container for the Literature Searching
pipeline for BRCA Exchange. The pipeline does the following:

- Download data files
- Get a list of PMIDs from PubMed for papers that mention "BRCA" in the title or abstract
- Run pubMunch on the PMIDs that have not previously been processed:
  - The crawler downloads HTML and PDF files for each PMID via publication APIs
  - The converter scrapes the HTML and PDFS files, creating raw text
  - The mutation finder uses regular expressions to find gene names (BRCA1 and BRCA2 in this case) and variant descriptions.

- Get a current list of BRCA variants from BRCA Exchange via its GA4GH instance
- Match variants found by pubMunch to the variants in BRCA Exchange
- Outputs a JSON file with the list of papers containing each variant, with their PMID, title, abstract, and other information.

To run the pipeline, docker must be installed on your sysetem. You can build the container by running 

```make```

The docker container can be invoked with the below command, where `<username>` and `<password>`
are Synapse credentials that have write access to the BRCA Exchange Literature Searching folder

```docker run quay.io/almussel/pubmunch-docker -u <username> -p <password>```

In order to get full functionality of the pipeline, it should be run on a
server with institutional credentials to allow access to publications. A
proxy can also be passed to `docker run` with the option

```--env http_proxy="http://user:password@host:port"```

The container can also be run with Synapse credentials so the results are uploaded
to the BRCA Exchange Literature Searching folder, as follows:

```docker run quay.io/almussel/pubmunch-docker -u <username> -p <password>```

Without these credentials, the output of the pipeline will be stored locally.

To run the pipeline on a small sample of 20 pmids, use the `-t` option. 
