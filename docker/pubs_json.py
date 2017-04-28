# Audrey Musselman-Brown
# 

import sys
import json
import re
import os
from ga4gh.client import client

BRCA_GA4GH_URL = "http://brcaexchange.org/backend/data/ga4gh/v0.6.0a7/" # URL for BRCA Exchange GA4GH instance

# BRCA 1 and 2 locations
BRCA1_NAME = "BRCA1"
BRCA1_CHR = "chr17"
BRCA1_START = 41160094
BRCA1_END = 41322387

BRCA2_NAME = "BRCA2"
BRCA2_CHR = "chr13"
BRCA2_START = 32889080
BRCA2_END = 32974403



GENE_BUFFER = 5

class Gene (object):

    def __init__(self, name, chromosome, start, end):
        object.__init__(self)
        self.name = name
        self.chromosome = chromosome
        self.start = start
        self.end = end

def build_variant_alias_dictionary(gene):

    ga4gh_client = client.HttpClient(BRCA_GA4GH_URL)
    variant_aliases = {}
    variant_count = 0
    for variant in ga4gh_client.search_variants(reference_name=gene.chromosome,
                                     variant_set_id="brca-hg37",
                                     start=gene.start-GENE_BUFFER,
                                     end=gene.end+GENE_BUFFER):
        variant_count += 1
        for name in variant.names:
             variant_aliases[name]= variant.id
        if len(variant.info["HGVS_cDNA"]) > 1:
            print variant.info["HGVS_cDNA"][0], type(variant.info["HGVS_cDNA"][0])
            sys.exit()
        if variant_count % 100 == 0:
            "Downloading BRCA variants:", variant_count, gene.name, "variants downloaded"
        variant_aliases[str(variant.info["HGVS_cDNA"][0])] = variant.id
        variant_aliases[str(variant.info["HGVS_Protein"][0])] = variant.id
    print "VARIANT COUNT IS: ", variant_count
    return variant_aliases

def build_variant_pubs_dictionary(filename, variant_aliases):

    variants = open(filename)
    header = variants.readline()

    variantD = {}

    for line in variants:
        line = line.strip().split('\t')
        if len(line) < 2:
           continue
        geneName = line[19]
        protName = line[15]
        varNames = line[10].split('|')
        numMentions = len(line[26].split(","))
        pmid = line[0]
        confirmed = line[1]

        if geneName not in ["BRCA1", "BRCA2"]:
            print "Non-BRCA gene: " + str(line)
            continue
        found = False
        for varName in varNames:
            if "None" in varName:
                varName = re.sub(r'([ACTG])>None', r'del\1', varName)
            if varName in variant_aliases[geneName]:
                varID = variant_aliases[geneName][varName]
                print "Found variant in BRCA-Exchange!"
                found = True
            elif protName in variant_aliases[geneName]:
                varID = variant_aliases[geneName][protName]
                print "Found variant in BRCA-Exchange!"
                found = True
            else:
                if not found:
                    print "Could not find variant in BRCA-Exchange: "+str(confirmed) + " " +str(geneName) + " " +  str(varName)

                continue

            if varID not in variantD:
                variantD[varID] = {pmid: numMentions}
            else:
                if pmid in variantD[varID]:
                    variantD[varID][pmid] = max(variantD[varID][pmid], numMentions)
                else:
                    variantD[varID][pmid] = numMentions

    return variantD

def ncbi_url(pmid):

    return "https://www.ncbi.nlm.nih.gov/pubmed/%s" % pmid


def build_pubs_dictionary(filename):

    pubs = open(filename)
    header = pubs.readline()

    pubsD = {}

    for line in pubs:
        line = line.strip().split('\t')    
        pmid = line[21]
        pubsD[pmid] = {"journal": line[5],
                       "year": line[9],
                       "authors": line[12],
                       "keywords": line[15],
                       "title": line[16],
                       "abstract": line[17],
                       "url": line[24] if line[24] != "" else ncbi_url(pmid)}
        
    return pubsD        

def main(args):
    
    variantFile = args[0]
    pubsFile = args[1]
    outFile = args[2]
    brcaFile = "/work/brcavars.json"

    brca1 = Gene(BRCA1_NAME, BRCA1_CHR, BRCA1_START, BRCA1_END)
    brca2 = Gene(BRCA2_NAME, BRCA2_CHR, BRCA2_START, BRCA2_END)
    
    if os.path.isfile(brcaFile):
        variant_aliases = json.loads(open(brcaFile).read())
    else:
        variant_aliases = {}
        variant_aliases["BRCA1"] = build_variant_alias_dictionary(brca1)
        variant_aliases["BRCA2"] = build_variant_alias_dictionary(brca2)
        f = open(brcaFile, 'w')
        f.write(json.dumps(variant_aliases))

    variantD = build_variant_pubs_dictionary(variantFile, variant_aliases)

    pubsD = build_pubs_dictionary(pubsFile)

    for variant in variantD:
        for pub in variantD[variant]:
            mentions = variantD[variant][pub]
            variantD[variant][pub] = pubsD[pub]
            variantD[variant][pub]["mentions"] = mentions

    output = json.dumps(variantD)

    out = open(outFile, 'w')
    out.write(output)

if __name__=="__main__":
    sys.exit(main(sys.argv[1:]))
