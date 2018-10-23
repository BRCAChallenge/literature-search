"""
Correlate variants from the built output of the BRCA Exchange with
variants found in articles from pubMunch
"""
import csv
import json
import sqlite3

import pandas as pd

import hgvs.parser
import hgvs.dataproviders.uta
import hgvs.assemblymapper


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
            # if row["varId"]:
            #     # TODO: what differentiates this from when a found variant is unconfirmed?
            #     stats["novarid"] += 1
            #     continue
            # if row["isConfirmed"] != "confirmed":
            #     # found variant could not be grounded
            #     # ie matched known reference sequence in BRCA1/BRCA2
            #     stats["notconfirmed"] += 1
            #     continue
            # hgvs_codings = row["hgvsCoding"].split("|") + \
            #     row["hgvsRna"].split("|") + row["hgvsProt"].split("|")
            if row["hgvsCoding"]:
                hgvs_codings = row["hgvsCoding"].split("|")
            else:
                hgvs_codings = []
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


def load():
    """
    Load artciles found by the crawler into a pandas dataframe
    and load variants from BRCA Exchange's built tsv
    indexed by variant in HGVS format
    """
    articles = pd.read_table("/crawl/mutations.tsv",
                             header=0,
                             usecols=["chrom", "start", "end", "hgvsProt", "hgvsCoding", "hgvsRna"])

    variants = pd.read_table("/references/output/release/built_with_change_types.tsv",
                             header=0,
                             usecols=["pyhgvs_Genomic_Coordinate_38",
                                      "pyhgvs_cDNA", "Chr", "Pos", "Ref", "Alt"]
                             ).set_index("pyhgvs_Genomic_Coordinate_38")

    return articles, variants


if __name__ == "__main__":
    print("Loading articles and variants...")
    articles, variants = load()
    print("Found {} articles entries and {} variants".format(articles.shape[0], variants.shape[0]))

    parser = hgvs.parser.Parser()
    server = hgvs.dataproviders.uta.connect()
    mapper = hgvs.assemblymapper.AssemblyMapper(server, assembly_name="GRCh37")

    # Generate a correctly formated genomic hgvs string
    print("Normalizing variants...")
    variants["hgvs"] = variants.apply(
        lambda row:
        "chr{}:g.{}{}>{}".format(row.Chr, row.Pos, row.Ref, row.Alt)
        if (len(row.Ref) == 1) and (len(row.Alt) == 1) else
        "chr{}:g.{}del{}ins{}".format(row.Chr, row.Pos, row.Ref, row.Alt),
        axis="columns")

    # Normalize the hgvs string by parsing via the hgvs package
    variants["hgvs"] = variants.apply(
        lambda row: str(parser.parse_hgvs_variant(row.hgvs)), axis="columns")

    # For each variant found in articles try to parse via hgvs
    print("Normalizing article hgvs mentions...")
    for article in articles["hgvsCoding"].fillna(""):
        for candidate in article.split("|"):
            try:
                parsed = parser.parse_hgvs_variant(candidate)
                print("Parsed:", candidate, parsed)
                try:
                    if parsed.type == "c":
                        mapped = mapper.c_to_g(parsed)
                        print("Mapped:", mapped)
                except hgvs.exceptions.HGVSInvalidVariantError:
                    print("Failed Mapping:", parsed)
            except hgvs.exceptions.HGVSParseError:
                print("Failed Parsing:", candidate)
