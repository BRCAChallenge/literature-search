"""
Normalize mentions of variants found in articles by pubMunch and BRCA Exchange
to genomic coordinates.
"""
import re
import sqlite3

import pandas as pd

import hgvs.parser
import hgvs.dataproviders.uta
import hgvs.assemblymapper


def load(articles_path, mentions_path, variants_path):
    """
    Load articles and mentions found by the crawler as well as
    variants in BRCA Exchange into pandas dataframes.
    """
    connection = sqlite3.connect(articles_path)
    articles = pd.read_sql_query("SELECT * FROM articles", connection)

    # Only load mentions that have coding hgvs at this point
    mentions = pd.read_table(mentions_path, header=0,
                             usecols=["docId", "hgvsCoding", "mutSnippets"]
                             ).dropna(subset=["hgvsCoding"])

    variants = pd.read_table(variants_path, header=0,
                             # nrows=1000,
                             usecols=["pyhgvs_Genomic_Coordinate_38",
                                      "pyhgvs_cDNA", "Chr", "Pos", "Ref", "Alt"])

    return articles, mentions, variants


def hgvs_c_to_g(candidate, parser, mapper):
    """
    Try to parse candidate hgvs coding string from a paper and if
    successful try and map it to an hgvs genomic string.
    Returns the parsed coding and mapped genomic hgvs
    """
    print(candidate)
    # Normalize single deletions: NM_007300.3:c.1100C>None -> NM_007300.3:c.1100del
    candidate = re.sub(r"(NM.*c\.\d*)([ATCG]>None)", r"\1del", candidate)

    # TODO: Normalize multiple deletions and delins
    # TODO: Limit to only specific BRCA transcripts
    # ex: 23199084	NM_007294.3:c.2681AA>None|NM_007300.3:c.2681AA>None

    print("=> {}".format(candidate))
    # Try to parse and map back to genomic
    try:
        parsed_hgvs = parser.parse_hgvs_variant(candidate)
        print("=> {}".format(parsed_hgvs))
        try:
            if parsed_hgvs.type == "c":
                norm_g_hgvs = mapper.c_to_g(parsed_hgvs)
                print("=> {}".format(norm_g_hgvs))
                return parsed_hgvs, norm_g_hgvs
            else:
                print("Only coding variants (.c) supported")
        except hgvs.exceptions.HGVSInvalidVariantError:
            print("Failed Mapping: HGVSInvalidVariantError")
        except hgvs.exceptions.HGVSInvalidIntervalError:
            print("Failed Mapping: HGVSInvalidIntervalError")
    except hgvs.exceptions.HGVSParseError:
        print("Failed Parsing")

    return None, None


def normalize_mentions(mentions, variants, parser, mapper):
    """
    Return a tuple list of (pmid, hgvs, mention) for all candidate
    hgvs found that parse and map.
    """
    def next_mention():
        for i, row in mentions.iterrows():
            print("============================================================")
            print("hgvsCoding:", row.hgvsCoding)
            print("mutSnippets:", row.mutSnippets)
            assert row.mutSnippets
            if type(row.mutSnippets) != str:
                print("mutSnippets is not a string")
                continue
            for candidate in row.hgvsCoding.split("|"):
                try:
                    norm_c_hgvs, norm_g_hgvs = hgvs_c_to_g(candidate, parser, mapper)
                except hgvs.exceptions.HGVSDataNotAvailableError:
                    print("Failed Conversion: HGVSDataNotAvailableError ")
                    continue
                if norm_g_hgvs:
                    print("Found in build: {}".format(str(norm_g_hgvs) in variants.index))
                    yield (str(norm_g_hgvs), str(norm_c_hgvs), row.docId, row.mutSnippets)

    # For each mention try to parse and normalize the hgvs
    return pd.DataFrame(
        [m for m in next_mention()],
        columns=["norm_g_hgvs", "norm_c_hgvs", "pmid", "snippet"]
    )


def normalize_variants(variants, parser, mapper):
    # Generate normalized genomic and coding hgvs strings
    # REMIND: This NC_0000<chr>.11 is a hack, will not work correctly
    # for single digit chromosomes...
    variants["norm_g_hgvs"] = variants.apply(
        lambda row:
        "NC_0000{}.11:g.{}{}>{}".format(
            row.Chr, row.Pos, row.Ref, row.Alt)
        if (len(row.Ref) == 1) and (len(row.Alt) == 1) else
        "NC_0000{}.11:g.{}_{}del{}ins{}".format(
            row.Chr, row.Pos, row.Pos + len(row.Ref), row.Ref, row.Alt),
        axis="columns")
    # Normalize the hgvs string by parsing via the hgvs package
    variants["norm_g_hgvs"] = variants.apply(
        lambda row: str(parser.parse_hgvs_variant(row.norm_g_hgvs)), axis="columns")

    return variants


if __name__ == "__main__":
    print("Loading articles, mentions and variants...")
    articles, mentions, variants = load(
        "/crawl/download/articles.db",
        "/crawl/mutations.tsv",
        "/references/output/release/built_with_change_types.tsv")

    print("Found {} articles {} mentions and {} variants".format(
        articles.shape[0], mentions.shape[0], variants.shape[0]))

    # Normalize and write intermediate files for exploration in jupyter
    print("Connecting to hgvs server and mappers...")
    parser = hgvs.parser.Parser()
    server = hgvs.dataproviders.uta.connect()
    mapper = hgvs.assemblymapper.AssemblyMapper(server, assembly_name="GRCh38")

    print("Normalizing variants...")
    variants = normalize_variants(variants, parser, mapper)
    variants = variants.set_index("norm_g_hgvs", drop=True)
    variants.to_csv("/crawl/variants-normalized.tsv", sep="\t")

    print("Normalizing mentions...")
    mentions = normalize_mentions(mentions, variants, parser, mapper)
    mentions = mentions.set_index("norm_g_hgvs", drop=True)
    mentions.to_csv("/crawl/mentions-normalized.tsv", sep="\t")
