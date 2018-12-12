#!/usr/bin/env bash

synapseDataDir=syn8520180
out=pubMunchData

usage () {
    echo "Usage: $0 -u <synapseUsername> -p <synapsePassword> [outputDir]"
    echo -e "\t(outputDir defaults to ./pubMunchData)"
}
while getopts u:p: option
do
    case "${option}"
        in
            u) synapseUsername=${OPTARG};;
            p) synapsePassword=${OPTARG};;
    esac
done

if [[ -z $synapseUsername ]] || [[ -z $synapsePassword ]]
then
    usage
    exit 1
fi

shift $((OPTIND -1))

if [[ -n $1 ]]
then
    out=$1
fi

synapse login -u $synapseUsername -p $synapsePassword --rememberMe
synapse get -r $synapseDataDir --downloadLocation $out

