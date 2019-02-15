"""
Normalize BRCA Exchange variants by parsing and mapping using the HGVS library
"""
import re
import pandas as pd

import hgvs.parser
import hgvs.dataproviders.uta
import hgvs.assemblymapper


def hgvs_c_to_g(candidate, parser, mapper):
    """
    Try to parse candidate hgvs coding string from a paper and if
    successful try and map it to an hgvs genomic string.
    Returns the parsed coding and mapped genomic hgvs
    """
    print(candidate)
    # Normalize single deletions: NM_007300.3:c.1100C>None -> NM_007300.3:c.1100del
    # candidate = re.sub(r"(NM.*c\.\d*)([ATCG]>None)", r"\1del", candidate)
    # Normalize single deletions: NM_007300.3:c.1100C>None -> NM_007300.3:c.1100delC
    candidate = re.sub(r"(NM.*c\.\d*)([ATCG])>None", r"\1del\2", candidate)

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
                return str(parsed_hgvs), str(norm_g_hgvs)
            else:
                print("Only coding variants (.c) supported")
        except hgvs.exceptions.HGVSInvalidVariantError:
            print("Failed Mapping: HGVSInvalidVariantError")
        except hgvs.exceptions.HGVSInvalidIntervalError:
            print("Failed Mapping: HGVSInvalidIntervalError")
    except hgvs.exceptions.HGVSParseError:
        print("Failed Parsing")

    return "", ""


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


def normalize_mentions(mentions, parser, mapper):
    """
    Return a tuple list of (pmid, hgvs, mention) for all candidate
    hgvs found that parse and map.
    """
    # mentions = mentions.drop_duplicates(["hgvsProt", "hgvsCoding", "mutSnippets"])
    mentions = mentions.drop_duplicates(["mutSnippets"])

    def norm_mention(row):
        print("============================================================")
        print("hgvsCoding:", row.hgvsCoding)
        print("mutSnippets:", row.mutSnippets.encode('utf8'))

        if not row.mutSnippets or type(row.mutSnippets) != str:
            print("mutSnippets is null or not a string")
            return ""

        for candidate in row.hgvsCoding.split("|"):
            try:
                norm_c_hgvs, norm_g_hgvs = hgvs_c_to_g(candidate, parser, mapper)
            except hgvs.exceptions.HGVSDataNotAvailableError:
                print("Failed Conversion: HGVSDataNotAvailableError ")
                continue
            if norm_g_hgvs:
                print("Success", norm_c_hgvs, norm_g_hgvs)
                return norm_g_hgvs
        return ""

    mentions["norm_g_hgvs"] = mentions.apply(norm_mention, axis=1)
    return mentions


if __name__ == "__main__":
    print("Connecting to hgvs server and mappers...")
    parser = hgvs.parser.Parser()
    server = hgvs.dataproviders.uta.connect()
    mapper = hgvs.assemblymapper.AssemblyMapper(server, assembly_name="GRCh38")

    print("Loading variants...")
    variants = pd.read_csv("/crawl/output/release/built_with_change_types.tsv",
                           sep="\t", header=0,
                           usecols=["pyhgvs_Genomic_Coordinate_38",
                                    "pyhgvs_cDNA", "Chr", "Pos", "Ref", "Alt", "Synonyms"])
    print("Found {} variants".format(variants.shape[0]))

    print("Normalizing variants...")
    variants = normalize_variants(variants, parser, mapper)
    variants = variants.set_index("norm_g_hgvs", drop=True)
    variants.to_csv("/crawl/variants-normalized.tsv", sep="\t")

    # print("Loading mentions...")
    # mentions = pd.read_csv("/crawl/mutations-trimmed.tsv",
    #                        sep="\t", header=0, dtype="str").fillna("")
    # print("Found {} mentions".format(mentions.shape[0]))

    # print("Normalizing mentions...")
    # mentions = normalize_mentions(mentions, parser, mapper)
    # mentions.to_csv("/crawl/mentions-normalized.tsv", sep="\t")
