#!/usr/bin/env python

"""
literature-search

Crawl, download and extract variants from pubmed using Maximilian Haeussler's
https://github.com/maximilianh/pubMunch and then match them to variants
in https://github.com/maximilianh/pubMunch.
"""

import os
import datetime
import io
import requests
import tarfile
import subprocess
import xml.etree.ElementTree
import click


def run(command):
    """ Run a script synchronously in a sub-process piping its output back to ours """
    process = subprocess.Popen(
        command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True, close_fds=True)
    for line in process.stdout:
        click.echo(line.rstrip(), err=True)


@click.group()
@click.option("--debug/--no-debug", default=False,
              help="Generate debug output")
@click.option("--pmid", default="",
              help="PMID to crawl")
@click.pass_context
def cli(ctx, debug, pmid):
    ctx.obj = {"debug": debug, "pmid": pmid}


@cli.command(help="Download references")
def references():
    run("./references.sh")


@cli.command(help="Update list of variants and pubmed ids")
@click.pass_context
def update(ctx):
    print("Updating list of variants from BRCA Exchange...")
    # url = "https://brcaexchange.org/backend/downloads/releases/current_release.tar.gz"
    url = "http://brcaexchange-prod.gi.ucsc.edu/backend/downloads/releases/current_release.tar.gz"
    response = requests.get(url)
    response.raise_for_status()
    results = tarfile.TarFile(fileobj=io.BytesIO(response.content))
    buf = results.extractfile("output/release/built_with_change_types.tsv")
    with open("/crawl/built_with_change_types.tsv", "wb") as f:
        f.write(buf.read())

    os.makedirs("/crawl", exist_ok=True)
    if ctx.obj["pmid"]:
        with open("/crawl/pmids.txt", "w") as f:
            f.write(ctx.obj["pmid"])
    else:
        print("Updating list of pubmed ids from NCBI NLM...")
        url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?" + \
            "db=pubmed&tool=retrPubmed&term=brca%2A[Title/Abstract]&retstart=0&retmax=9999999"
        response = requests.get(url)
        response.raise_for_status()
        root = xml.etree.ElementTree.fromstring(response.content)
        assert root[3].tag == "IdList", root[3].tag
        with open("/crawl/pmids.txt", "w") as f:
            f.write("\n".join([ID.text for ID in root[3]]))
    with open("/crawl/pubs-date.txt", "w") as f:
        f.write(datetime.datetime.now().isoformat(timespec="seconds"))


@cli.command(help="Download papers")
@click.pass_context
def download(ctx):
    print("Downloading papers...")
    run("python2 -u /pubMunch/pubCrawl2 -u{} --forceContinue /crawl".format(
        "dv" if ctx.obj["debug"] else "") + " 2>&1 | tee /crawl/download-log.txt")


@cli.command(help="Convert papers to text")
@click.pass_context
def convert(ctx):
    print("Converting papers to text...")
    run("python2 -u /pubMunch/pubConvCrawler /crawl /crawl/text" +
        " 2>&1 | tee /crawl/convert-log.txt")


@cli.command(help="Find variants in all papers text")
@click.pass_context
def find(ctx):
    print("Finding variants...")
    run("cp -r /pubMunch/data/* /references/")  # Update regex in case its changed
    run("python2 -u /pubMunch/pubFindMutations {} /crawl/text /crawl/mutations.tsv".format(
        "-d" if ctx.obj["debug"] else "") + " 2>&1 | tee /crawl/find-log.txt")


@cli.command(help="Match variants to papers")
@click.pass_context
def match(ctx):
    print("Matching variants...")
    # Trim so pandas can ingest easily
    run("head -n -3 /crawl/mutations.tsv > /crawl/mutations-trimmed.tsv")
    run("python3 -u /app/match.py 2>&1 | tee /crawl/match-log.txt")


@cli.command(help="Export literature.json")
@click.pass_context
def export(ctx):
    print("Exporting literature.json...")
    run("python3 -u /app/export.py /crawl")


@cli.command(help="Generate stats for current crawl")
@click.pass_context
def stats(ctx):
    run("CRAWL_PATH=/crawl jupyter nbconvert"
        + " --execute stats.ipynb --ExecutePreprocessor.timeout=None"
        + " --to asciidoc --stdout --template ascii.tpl")


@cli.command(help="Crawl latest papers...")
@click.pass_context
def crawl(ctx):
    ctx.invoke(update)
    ctx.invoke(download)
    ctx.invoke(convert)
    ctx.invoke(find)
    ctx.invoke(match)
    ctx.invoke(export)
    ctx.invoke(stats)
    print("Done.")


if __name__ == "__main__":
    cli()
