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

while getopts u:p:t option
do
        case "${option}"
        in
                u) synapseUsername=${OPTARG};;
                p) synapsePassword=${OPTARG};;
                t) test=true;;
        esac
done

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

#mkdir $workdir/pubMunch/data
synapse get -r $synapseDataDir --downloadLocation $workdir/pubMunch/data
#cp -r /home/joe/pmdata $workdir/pubMunch/data

mkdir $workdir/Crawl $workdir/CrawlText

# Pubmed API url: Retrieve all articles that mention "brca" in the title or abstract
pubmedURL="https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&tool=retrPubmed&email=maximilianh@gmail.com&term=brca%2A[Title/Abstract]&retstart=0&retmax="$numPMIDs

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

echo "Uploading PubMunch results"
cp $workdir/allPmids.txt $workdir/crawledPmids.txt

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

if [ -d /dockerOutput ]
    then
        cp -r $workdir /dockerOutput/
fi

