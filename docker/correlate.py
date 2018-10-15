"""
Correlate variants from the built output of the BRCA Exchange with
variants found in articles from pubMunch
"""
import sys
import csv
import json
import sqlite3


def get_articles(article_file):
    """ get article metadata, return a dict using article PMID as key """
    articles = {}
    conn = sqlite3.connect(article_file)
    # conn.row_factory = dict_factory
    conn.row_factory = lambda cursor, row: {
        col[0]: row[idx] for idx, col in enumerate(cursor.description)}
    curs = conn.cursor()
    for article in curs.execute("SELECT * FROM articles"):
        pmid = article["pmid"]
        articles[str(pmid)] = article
    return articles


def get_known_variants(release_file):
    """
    Get known Brca Exchange variants from latest release,
    return a dict mapping from pyhgvs names to genomic coordinates (hg38)
    """
    built_pyhgvs = {}
    with (open(release_file)) as built:
        variants = csv.DictReader(built, delimiter="\t")
        for variant in variants:
            built_pyhgvs[variant["pyhgvs_cDNA"]] = variant["Genomic_Coordinate_hg38"]
            # strip "uncertainty" parens from protein nomenclature
            built_pyhgvs[variant["pyhgvs_Protein"].replace('(', '').replace(')', '')] = \
                variant["Genomic_Coordinate_hg38"]
    return built_pyhgvs


def test_duplicate(matches, variant):
    """ test if a matched found variant is already associated with a given BRCA Exchange variant """
    for match in matches:
        # if the pmid (listed as 'varId' in found variants table)
        # is already present for the given BRCA exchange variant,
        # then this is a duplicate
        if variant["varId"] == match["varId"]:
            return True
    return False


def correlate_found_variants(found_file, built_pyhgvs):
    """ match variants found in text to variants in BRCA Exchange """
    matches = {}
    stats = {"tried": 0, "novarid": 0, "notconfirmed": 0, "duplicates": 0, "matched": 0}
    with (open(found_file)) as found:
        found_variants = csv.DictReader(found, delimiter="\t")
        for row in found_variants:
            stats["tried"] += 1
            if row["varId"]:
                # TODO: what differentiates this from when a found variant is unconfirmed?
                stats["novarid"] += 1
                continue
            if row["isConfirmed"] != "confirmed":
                # found variant could not be grounded
                # ie matched known reference sequence in BRCA1/BRCA2
                stats["notconfirmed"] += 1
                continue
            hgvs_codings = row["hgvsCoding"].split("|") + \
                row["hgvsRna"].split("|") + row["hgvsProt"].split("|")
            for coding in hgvs_codings:
                if coding in built_pyhgvs:
                    genomic_name = built_pyhgvs[coding]
                    if genomic_name not in matches:
                        matches[genomic_name] = []
                    if test_duplicate(matches[genomic_name], row):
                        stats["duplicates"] += 1
                    else:
                        matches[genomic_name].append(row)
                        stats["matched"] += 1
    return (matches, stats)


def filter_articles(articles, matches):
    """ filter articles to only those matched to a variant """
    filtered_articles = {}
    stats = {"noarticledata": 0}
    for _, variant_matches in matches.iteritems():
        for match in variant_matches:
            doc_id = match["docId"]
            if doc_id not in articles:
                stats["noarticledata"] += 1
            elif doc_id not in filtered_articles:
                filtered_articles[doc_id] = articles[doc_id]
    return (filtered_articles, stats)


def correlate(article_file, release_file, found_file, output_file):
    """ For each variant find all matching articles """
    stats = {}
    print("Building articles dictionary")
    articles = get_articles(article_file)
    print("Building variants dictionary")
    built_pyhgvs = get_known_variants(release_file)
    print("Correlating found variants to known variants")
    matches, correlation_stats = correlate_found_variants(found_file, built_pyhgvs)
    stats.update(correlation_stats)
    print("Filtering articles to only those relevant to known mutations")
    filtered_articles, filter_stats = filter_articles(articles, matches)
    stats.update(filter_stats)
    print("Writing {0}".format(output_file))
    with open(output_file, "w") as output:
        output.write(json.dumps(
            {"papers": filtered_articles,
             "paperCount": len(filtered_articles),
             "variants": matches,
             "variantCount": len(matches),
             "stats": stats}))
    print("Success. Stats:")
    print(stats)


if __name__ == "__main__":
    if len(sys.argv[1:]) != 4:
        sys.exit("usage: python correlate.py [article db] [brca release] [found mutations] [output]")
    correlate(*sys.argv[1:])
