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
