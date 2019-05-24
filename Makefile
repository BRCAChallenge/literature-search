IMAGE_NAME = $(USER)-literature-search

build:
	# Build and tag the image prefixed by user to avoid conflicts on shared machines
	docker build --no-cache -t $(IMAGE_NAME) .

push:
	# Tag and push our current docker build to dockerhub
	docker tag $(USER)-literature-search:latest brcachallenge/literature-search:latest
	docker push brcachallenge/literature-search:latest

debug:
	# Run the docker mapping local directory into app for development
	docker run --rm -it \
		--name $(IMAGE_NAME) \
		--user=`id -u`:`id -g` \
		-e HOME=/app \
		-v `readlink -f ~/pubConf`:/.pubConf:ro \
		-v `readlink -f ~/data/literature-search/references`:/references \
		-v `readlink -f ~/data/literature-search/crawl`:/crawl \
		-v `pwd`:/app \
		--entrypoint /bin/bash \
	  $(IMAGE_NAME)

update-pubmunch:
	# Fetch upstream master and merge into our fork
	cd ~/pubMunch && \
	git fetch upstream && \
	git checkout master && \
	git merge upstream/master && \
	git checkout brca && \
	git rebase master

references:
	# Run image on command line to download all references
	docker run --rm -it \
		--name $(IMAGE_NAME) \
		--user=`id -u`:`id -g` \
		-v `readlink -f ~/.pubConf`:/.pubConf:ro \
		-v `readlink -f ~/data/literature-search/references`:/references \
		-v `readlink -f ~/data/literature-search/crawl`:/crawl \
	  $(IMAGE_NAME) references

crawl-one:
	# Run image on command line fully automated generate literature.json for one paper
	docker run --rm -it \
		--name $(IMAGE_NAME) \
		--user=`id -u`:`id -g` \
		-v `readlink -f ~/pubConf`:/.pubConf:ro \
		-v `readlink -f ~/data/literature-search/references`:/references \
		-v `readlink -f ~/data/literature-search/crawl`:/crawl \
	  $(IMAGE_NAME) --pmid 9042909 crawl
