#!/usr/bin/env bash

set -e

workdir=/tmp
optdir=/opt
#workdir=/home/joe/pmwork-newoutput
#optdir=/home/joe/pubMunch-BRCA/docker
numPMIDs=9999999
synapseDir=syn8506589
synapseOutDir=$synapseDir
synapseDataDir=syn8520180
pmidFile=syn8683574
mutationFile=syn8683582
articleFile=syn11257493
test=false
cmd=munch

while getopts u:p:t option
do
        case "${option}"
        in
                u) synapseUsername=${OPTARG};;
                p) synapsePassword=${OPTARG};;
                t) test=true;;
        esac
done

shift $((OPTIND -1))

# commands:
#   munch - run the full pipeline
#   test - perform test run of full pipeline over a small list of papers

if [[ -n $1 ]]
then
    cmd=$1
fi

if [ $cmd = unittest ]
then
    TESTDIR=$optdir/brca_tests python $optdir/test_correlate.py
    exit
fi

if $test
  then
    numPMIDs=25
    synapseDir=syn8532321
    synapseOutDir=syn9620237
    pmidFile=syn8532670
    mutationFile=syn8532671
fi

if [ -d /dockerOutput ]
    then
        echo Touching /dockerOutput/test
        touch /dockerOutput/test
fi

$optdir/download.sh

# Download data from Synapse to /workdir/pubMunch/data

if [ -n $synapseUsername ] && [ -n $synapsePassword ]
  then
   synapse login -u $synapseUsername -p $synapsePassword --rememberMe
   loggedIn=true
fi

if [ -d /data ]
    then
        echo Copying data
        cp -R /data $workdir/pubMunch/data
    else
        echo Downloading data
        $optdir/download_data.sh -u $synapseUsername -p $synapsePassword $workdir/pubMunch/data
fi

mkdir $workdir/Crawl $workdir/CrawlText

# Pubmed API url: Retrieve all articles that mention "brca" in the title or abstract
pubmedURL="https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&tool=retrPubmed&email=maximilianh@gmail.com&term=brca%2A[Title/Abstract]&retstart=0&retmax="$numPMIDs

if [ $cmd = "test" ]
then
    cp $optdir/brca_tests/pmids.txt $workdir/Crawl/pmids.txt
else
    # Retrieve list of papers from PubMed
    wget -O $workdir/pubmedResponse.xml $pubmedURL

    # Extract PMIDs from xml response
    python $optdir/getpubs.py $workdir/pubmedResponse.xml > $workdir/allPmids.txt

    # Download list of previously crawled PMIDs from synapse
    synapse get $pmidFile --downloadLocation $workdir
    #touch $workdir/crawledPmids.txt

    # Determine which PMIDs are new since the last run
    sort -i $workdir/allPmids.txt
    sort -i $workdir/crawledPmids.txt
    grep -F -x -v -f $workdir/crawledPmids.txt $workdir/allPmids.txt > $workdir/Crawl/pmids.txt
fi

if [[ $(wc -l $workdir/Crawl/pmids.txt | awk '{print $1}') -ge 1 ]]
  then 
    # Crawl the new PMIDs
    $workdir/pubMunch/pubCrawl2 -du --forceContinue $workdir/Crawl

    # Convert crawled papers to text
    $workdir/pubMunch/pubConvCrawler $workdir/Crawl $workdir/CrawlText

    # Find mutations in crawled papers
    $workdir/pubMunch/pubFindMutations $workdir/CrawlText $workdir/mutations.tsv
fi

# Download previously found mutations
synapse get $mutationFile --downloadLocation $workdir
#touch $workdir/foundMutations.tsv
#echo "this is a header line\n" > $workdir/foundMutations.tsv

#cat $workdir/foundMutations.tsv  <(tail -n +2 $workdir/mutations.tsv) > $workdir/all_mutations.tsv
#(head -n 1 $workdir/all_mutations.tsv && tail -n +2 $workdir/all_mutations.tsv | sort) > $workdir/foundMutations.tsv

if [ $cmd != "test" ]
then
    echo "Uploading PubMunch results"
    cp $workdir/allPmids.txt $workdir/crawledPmids.txt
fi

#if $loggedIn
#  then
#    # Update version number. This is necessary due to a Synapse upload issue
#    oldVersion=`head -1 $workdir/foundMutations.tsv | awk -F '\t' '{print $NF}'`
#    echo Old Version = $oldVersion
#    newVersion=$(expr $oldVersion + 1)
#    sed -i "1s/$oldVersion/$newVersion/g" $workdir/foundMutations.tsv
#    synapse add $workdir/foundMutations.tsv --parentId=$synapseOutDir
#    synapse add $workdir/crawledPmids.txt --parentId=$synapseOutDir
#fi

echo "Matching mutations to BRCA variants"
#if $test
#  then
#    synapse get syn8532322 --downloadLocation $workdir
#fi

#python $optdir/pubs_json.py $workdir/all_mutations.tsv $workdir/CrawlText/0_00000.articles $workdir/newPubs.json $workdir/variantPubs.json

python $optdir/correlate.py $workdir/CrawlText/articles.db $workdir/brca_release/output/release/built_with_change_types.tsv $workdir/mutations.tsv $workdir/litResults.json

#echo "Uploading mutations and pmids"
# Upload  output json file
#if $loggedIn
#  then
#    synapse add $workdir/BRCApublications.json --parentId=$synapseOutDir
#else
#    cat BRCApublications.json
#fi
echo "Success!"

if [ $cmd = "test" ]
then
    python $optdir/test_pipeline.py $workdir/litResults.json $optdir/brca_tests/expected.json
fi

if [ -d /dockerOutput ]
    then
        echo "Copying output"
        cp -r $workdir /dockerOutput/
fi

