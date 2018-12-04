# Host path where references should be stored - symlink tolerant
IMAGE_NAME = $(USER)-pubmunch-pipeline

build:
	# Build and tag the image prefixed by user to avoid conflicts on shared machines
	docker build --no-cache -t $(IMAGE_NAME) .

update-built:
	# Get latest released built file which we use as input to correlate
	wget -qO- https://brcaexchange.org/backend/downloads/releases/current_release.tar.gz \
		| tar xz -C /references/

uta:
	# Run local version of UTA storing database on host
	# docker network create rcurrie-pubmunch-network
	docker run --rm -it \
		--name $(USER)-uta \
		--network=$(USER)-pubmunch-network \
		-v `readlink -f ~/data/pubmunch/uta`:/var/lib/postgresql/data \
		biocommons/uta:uta_20170117

debug:
	# Run the docker mapping out of local directory for development
	docker run --rm -it \
		--name $(USER)-crawler \
		--network=$(USER)-pubmunch-network \
		--user=`id -u`:`id -g` \
		-e UTA_DB_URL=postgresql://anonymous@$(USER)-uta:5432/uta/uta_20170117 \
		-e HGVS_SEQREPO_DIR=/references/seqrepo/2018-10-03 \
		-v `readlink -f ~/.pubConf`:/.pubConf:ro \
		-v `readlink -f ~/data/pubmunch/references`:/references \
		-v `readlink -f ~/pubMunch`:/pubMunch \
		-v `readlink -f ~/data/pubmunch/crawl`:/crawl \
		-v `pwd`:/app \
		--entrypoint /bin/bash \
	  $(IMAGE_NAME)
			
get-pubs:
	# Get list of all pmids with BRCA in them
	wget -O /crawl/download/pmids.xml "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&tool=retrPubmed&email=maximilianh@gmail.com&term=brca%2A[Title/Abstract]&retstart=0&retmax=9999999" 
	python getpubs.py /crawl/download/pmids.xml > /crawl/all_pmids.txt
	wc /crawl/all_pmids.txt
	# Run all
	cp /crawl/all_pmids.txt /crawl/download/pmids.txt
	# Pick 1000 at random
	# shuf -n 1000 /crawl/all_pmids.txt > /crawl/download/pmids.txt
	# cat /crawl/download/pmids.txt

clean:
	# Remove all crawl files and reset to single paper to download
	rm -rf /crawl/*
	mkdir -p /crawl/download
	echo 23199084 > /crawl/download/pmids.txt
	# echo 30186769 >> /crawl/download/pmids.txt
	
crawl: download convert find correlate

download:
	# Crawl the new PMIDs
	python /pubMunch/pubCrawl2 -duv --forceContinue /crawl/download 2>&1 | tee /crawl/download-log.txt

convert:
	# Convert crawled papers to text
	rm -rf /crawl/text/*
	python /pubMunch/pubConvCrawler /crawl/download /crawl/text 2>&1 | tee /crawl/convert-log.txt

find:
	# Find mutations in crawled papers
	# rm -rf /crawl/mutations.*
	python /pubMunch/pubFindMutations /crawl/text /crawl/mutations.tsv | tee /crawl/find-log.txt

correlate:
	# Match articles to mutations in BRCA Exchange
	python /app/correlate.py 2>&1 | tee /crawl/correlate-log.txt

references:
	# Unfinished download of big files - needs integration into others
	# that are maintained within the pubMunch repo
	cp -r /pubMunch/data/* /references/
	wget -qO- http://hgwdev.soe.ucsc.edu/~max/pubs/tools/bigFiles.tgz \
		| tar xfzv - -C /references --strip-components 1

	# Install large sequence database so hgvs runs local
	mkdir -p /references/seqrepo
	seqrepo -r /references/seqrepo pull -i 2018-10-03
	seqrepo --root-directory /references/seqrepo/ list-local-instances
	
	wget -N -P /references http://hgdownload.cse.ucsc.edu/goldenPath/hg19/bigZips/hg19.2bit
	wget -N -P /references http://hgdownload.cse.ucsc.edu/admin/exe/linux.x86_64/twoBitToFa
	chmod +x /references/twoBitToFa
	/references/twoBitToFa /references/hg19.2bit /references/variants/hg19.fa
	rm /references/hg19.2bit
