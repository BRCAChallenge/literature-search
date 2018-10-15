# Host path where references should be stored - symlink tolerant
IMAGE_NAME = $(USER)-pubmunch-pipeline

build:
	# Build and tag the image prefixed by user to avoid conflicts on shared machines
	docker build --no-cache -t $(IMAGE_NAME) .

update-built:
	# Get latest released built file which we use as input to correlate
	wget -N -P /data \
		https://brcaexchange.org/backend/downloads/releases/current_release.tar.gz
	tar -zxsvf /data/current_release.tar.gz -C /data --skip-old-files

debug:
	# Run the docker mapping out of local directory for development
	docker run --rm -it \
		--entrypoint /bin/bash \
		--user=`id -u`:`id -g` \
		-v `readlink -f ~/.pubConf`:/.pubConf:ro \
		-v `readlink -f ~/data/pubmunch/data`:/data \
		-v `readlink -f ~/data/pubmunch/crawl`:/crawl \
		-v `readlink -f ~/pubMunch`:/pubMunch \
		-v `pwd`:/app \
	  $(IMAGE_NAME)

clean:
	rm -rf /crawl/download/*
	rm -rf /crawl/text/*
	rm -rf /crawl/mutations.*
	echo 23199084 > /crawl/download/pmids.txt

crawl: download convert find

download:
	# Crawl the new PMIDs
	python /pubMunch/pubCrawl2 -du --forceContinue /crawl/download

convert:
	# Convert crawled papers to text
	python /pubMunch/pubConvCrawler /crawl/download /crawl/text

find:
	# Find mutations in crawled papers
	python /pubMunch/pubFindMutations /crawl/text /crawl/mutations.tsv

correlate:
	python /app/correlate.py \
		/crawl/text/articles.db \
		/data/output/release/built_with_change_types.tsv \
		/crawl/mutations.tsv /crawl/litResults.json

data:
	curl http://hgwdev.soe.ucsc.edu/~max/pubs/tools/bigFiles.tgz
	tar xfkv bigFiles.tgz

