IMAGE_NAME = $(USER)-literature-search

build:
	# Build and tag the image prefixed by user to avoid conflicts on shared machines
	docker build --no-cache -t $(IMAGE_NAME) .

update-pubmunch:
	# Fetch upstream master and merge into our fork
	cd ~/pubMunch && \
	git fetch upstream && \
	git checkout master && \
	git merge upstream/master && \
	git checkout brca && \
	git rebase master

debug:
	# Run the docker mapping local directory into app for development
	docker run --rm -it \
		--name $(IMAGE_NAME) \
		--user=`id -u`:`id -g` \
		-e HGVS_SEQREPO_DIR=/references/seqrepo/2018-10-03 \
		-v `readlink -f ~/.pubConf`:/.pubConf:ro \
		-v `readlink -f ~/data/literature-search/references`:/references \
		-v `readlink -f ~/data/literature-search/crawl`:/crawl \
		-v `pwd`:/app \
		--entrypoint /bin/bash \
	  $(IMAGE_NAME)

crawl: update-built get-pubs download convert find match

test:
	PMID=9042909 make clean
	make update-built download convert find match

clean:
	# Remove all crawl files and reset to single PMID to download
	rm -rf /crawl/*
	mkdir /crawl/download
	echo $(PMID) > /crawl/download/pmids.txt
	echo $(date --iso-8601=seconds) > /crawl/pubs-date.txt
	
update-built:
	# Get latest released built file which we use as input to correlate
	wget -qO- https://brcaexchange.org/backend/downloads/releases/current_release.tar.gz \
		| tar xz -C /crawl/

get-pubs:
	# Get list of all pmids with BRCA in them and save timestamp of crawl
	mkdir -p /crawl/download
	wget -O /crawl/download/pmids.xml "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&tool=retrPubmed&email=maximilianh@gmail.com&term=brca%2A[Title/Abstract]&retstart=0&retmax=9999999" 
	python2 getpubs.py /crawl/download/pmids.xml > /crawl/download/pmids.txt
	echo $(date --iso-8601=seconds) > /crawl/pubs-date.txt

download:
	# Crawl the new PMIDs
	python2 -u /pubMunch/pubCrawl2 -duv --forceContinue /crawl/download 2>&1 | tee /crawl/download-log.txt

convert:
	# Convert crawled papers to text
	python2 -u /pubMunch/pubConvCrawler /crawl/download /crawl/text 2>&1 | tee /crawl/convert-log.txt

find:
	# Find mutations in crawled papers
	# Update regext in case they have changed
	cp -r /pubMunch/data/* /references/
	python2 -u /pubMunch/pubFindMutations -d /crawl/text /crawl/mutations.tsv 2>&1 | tee /crawl/find-log.txt
	head -n -3 /crawl/mutations.tsv > /crawl/mutations-trimmed.tsv

match:
	# Match articles to mutations in BRCA Exchange and export literature.json
	python3 -u /app/match.py 2>&1 | tee /crawl/match-log.txt
