#!/usr/bin/env python

"""
literature-search

Crawl, download and extract variants from pubmed using Maximilian Haeussler's
https://github.com/maximilianh/pubMunch and then match them to variants
in https://github.com/maximilianh/pubMunch.
"""

import io
import requests
import tarfile
import subprocess
import xml.etree.ElementTree
import click


def run(command):
    """ Run a script synchronously in a sub-process piping its output back to ours """
    process = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
    while True:
        line = process.stdout.readline().rstrip()
        if line:
            click.echo(line, err=True)
        else:
            break


@click.group()
@click.option('--debug/--no-debug', default=False)
@click.pass_context
def cli(ctx, debug):
    ctx.obj = {"debug": debug}
    click.echo('Debug mode is %s' % ('on' if debug else 'off'))


@cli.command(help="Download references")
def references():
    run("./references.sh")


@cli.command(help="Update list of variants and pubmed ids")
def update():
    print("Updating list of variants from BRCA Exchange...")
    url = "https://brcaexchange.org/backend/downloads/releases/current_release.tar.gz"
    response = requests.get(url)
    results = tarfile.TarFile(fileobj=io.BytesIO(response.content))
    buf = results.extractfile("output/release/built_with_change_types.tsv")
    with open("/crawl/built_with_change_types.tsv", "wb") as f:
        f.write(buf.read())

    print("Updating list of pubmed ids from NCBI NLM...")
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?" + \
        "db=pubmed&tool=retrPubmed&term=brca%2A[Title/Abstract]&retstart=0&retmax=9999999"
    response = requests.get(url)
    root = xml.etree.ElementTree.fromstring(response.content)
    assert root[3].tag == "IdList", root[3].tag
    with open("/crawl/pmids.txt", "w") as f:
        f.write("\n".join([ID.text for ID in root[3]]))


if __name__ == "__main__":
    cli()
