"""
Correlate mentions of variants found in articles by pubMunch to variants in BRCA Exchange.
"""
import re
import sqlite3

import pandas as pd

import hgvs.parser
import hgvs.dataproviders.uta
import hgvs.assemblymapper

# def correlate(article_file, release_file, found_file, output_file):
#     """ For each variant find all matching articles """
#     stats = {}
#     print("Building articles dictionary")
#     articles = get_articles(article_file)
#     print("Building variants dictionary")
#     built_pyhgvs = get_known_variants(release_file)
#     print("Correlating found variants to known variants")
#     matches, correlation_stats = correlate_found_variants(found_file, built_pyhgvs)
#     stats.update(correlation_stats)
#     print("Filtering articles to only those relevant to known mutations")
#     filtered_articles, filter_stats = filter_articles(articles, matches)
#     stats.update(filter_stats)
#     print("Writing {0}".format(output_file))
#     with open(output_file, "w") as output:
#         output.write(json.dumps(
#             {"papers": filtered_articles,
#              "paperCount": len(filtered_articles),
#              "variants": matches,
#              "variantCount": len(matches),
#              "stats": stats}))
#     print("Success. Stats:")
#     print(stats)


def load(articles_path, mentions_path, variants_path):
    """
    Load articles and mentions found by the crawler as well as
    variants in BRCA Exchange into pandas dataframes.
    """
    connection = sqlite3.connect(articles_path)
    articles = pd.read_sql_query("SELECT * FROM articles", connection).set_index("pmid")

    mentions = pd.read_table(mentions_path, header=0,
                             usecols=["docId", "chrom", "start", "end",
                                      "hgvsProt", "hgvsCoding", "hgvsRna"]
                             ).set_index("docId")
    mentions.index.name = "pmid"

    variants = pd.read_table(variants_path, header=0,
                             usecols=["pyhgvs_Genomic_Coordinate_38",
                                      "pyhgvs_cDNA", "Chr", "Pos", "Ref", "Alt"]
                             ).set_index("pyhgvs_Genomic_Coordinate_38")

    return articles, mentions, variants


def normalize(mentions, variants):
    """
    Parse and normalize mentions and variants
    genomic HGVS.
    """
    print("Connecting to hgvs server and mappers...")
    parser = hgvs.parser.Parser()
    server = hgvs.dataproviders.uta.connect()
    mapper = hgvs.assemblymapper.AssemblyMapper(server, assembly_name="GRCh38")

    # For each mention try to parse and normalize the hgvs
    print("Normalizing mentions...")
    for mention in mentions["hgvsCoding"].fillna(""):
        for candidate in mention.split("|"):
            # Skip empty candidates
            if not candidate:
                continue
            print("\"{}\"".format(candidate))
            try:
                # Fix single deletions: NM_007300.3:c.1100C>None -> NM_007300.3:c.1100del
                candidate = re.sub(r"(NM.*c\.\d*)([ATCG]>None)", r"\1del", candidate)

                parsed = parser.parse_hgvs_variant(candidate)
                print("Parsed: {} into {}".format(candidate, parsed))
                try:
                    if parsed.type == "c":
                        mapped = mapper.c_to_g(parsed)
                        print("Mapped to {}".format(mapped))
                    else:
                        print("Only transcript supported")
                except hgvs.exceptions.HGVSInvalidVariantError:
                    print("Failed Mapping: HGVSInvalidVariantError")
                except hgvs.exceptions.HGVSInvalidIntervalError:
                    print("Failed Mapping: HGVSInvalidIntervalError")
            except hgvs.exceptions.HGVSParseError:
                print("Failed Parsing")

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

    return mentions, variants


if __name__ == "__main__":
    print("Loading articles, mentions and variants...")
    articles, mentions, variants = load(
        "/crawl/download/articles.db",
        "/crawl/mutations.tsv",
        "/references/output/release/built_with_change_types.tsv")

    print("Found {} articles {} mentions and {} variants".format(
        articles.shape[0], mentions.shape[0], variants.shape[0]))

    print("Normalizing mentions...")
    mentions, variants = normalize(mentions, variants)
