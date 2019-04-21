"""
Export matched variants to literature.json
"""
import sys
import datetime
import json
import sqlite3
import pandas as pd


def top_papers(mentions, pyhgvs):
    """ Return (pmid, points) tuple sorted by points against pyhgvs """
    top = mentions[mentions.pyhgvs_Genomic_Coordinate_38 == pyhgvs] \
        .groupby(["pyhgvs_Genomic_Coordinate_38", "pmid"]) \
        .agg({"points": sum}) \
        .sort_values("points", ascending=False)
    return top.reset_index()[["pmid", "points"]].values


def top_snippets(mentions, pyhgvs, pmid):
    """ Return list of top snippets for this variant and paper by points """
    paper = mentions[(mentions.pyhgvs_Genomic_Coordinate_38 == pyhgvs) & (mentions.pmid == pmid)]
    return [snippet
            for snippets in paper.sort_values("points", ascending=False).snippets.values
            for snippet in snippets.split("|")][:3]


def top_papers_and_snippets(mentions, pyhgvs):
    return [{"pmid": str(p[0]), "points": int(p[1]),
             "mentions": top_snippets(mentions, pyhgvs, p[0])}
            for p in top_papers(mentions, pyhgvs)]


if __name__ == "__main__":
    connection = sqlite3.connect("file:/crawl/download/articles.db?mode=ro", uri=True)
    articles = pd.read_sql_query("SELECT * FROM articles", connection)
    articles.pmid = articles.pmid.astype(str)
    print("{} articles loaded from the articles sqlite database".format(articles.shape[0]))

    mentions = pd.read_csv("/crawl/mentions-matched.tsv", sep="\t", encoding="utf-8")
    mentions.pmid = mentions.pmid.astype(str)
    print("Total matched mentions: {}".format(mentions.shape[0]))
    mentions = mentions.drop_duplicates(["pyhgvs_Genomic_Coordinate_38", "pmid", "snippets"])
    print("After dropping duplicates: {}".format(mentions.shape[0]))
    mentions.head()

    variants = {}

    remaining = mentions.pyhgvs_Genomic_Coordinate_38.unique().shape[0]
    print(datetime.datetime.now())
    for pyhgvs in mentions.pyhgvs_Genomic_Coordinate_38.unique():
        sys.stdout.write("Remaining: {}\r".format(remaining))
        sys.stdout.flush()
        variants[pyhgvs] = top_papers_and_snippets(mentions, pyhgvs)
        remaining -= 1

    lit = {
        "date": open("/crawl/pubs-date.txt").read().strip(),
        "papers": articles[articles.pmid.isin(mentions.pmid)].set_index(
            "pmid", drop=False).to_dict(orient="index"),
        "variants": variants
    }

    with open("/crawl/literature.json", "w") as output:
        output.write(json.dumps(lit, sort_keys=True))

    print("Exported {} variants in {} papers".format(
        len(lit["variants"].keys()), len(lit["papers"].keys())))

    with open("/crawl/literature.json") as f:
        lit = json.loads(f.read())
    print("{} Papers and {} Variants exported".format(len(lit["papers"]), len(lit["variants"])))
