import urllib2
import sys
import xml.etree.ElementTree as ET

pubmedURL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&tool=retrPubmed&email=maximilianh@gmail.com&term=brca%2A[Title/Abstract]&retstart=0&retmax=9999999"

def main(args):
    content = open(args[0]).read()
    root = ET.fromstring(content)
    assert root[3].tag == "IdList", root[3].tag
    ids = [ID.text for ID in root[3]]

    for ID in ids:
        print ID

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
