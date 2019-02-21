"""
Match variants found in papers to variants in BRCA Exchange
"""
import os
import re
import functools
# import itertools
import pandas as pd

import hgvs.parser
import hgvs.dataproviders.uta
import hgvs.assemblymapper


parser = None
mapper = None
mentions = None


@functools.lru_cache(maxsize=None)
def parse_and_map_hgvs(candidate):
    assert candidate

    # Normalize single deletions: NM_007300.3:c.1100C>None -> NM_007300.3:c.1100delC
    candidate = re.sub(r"(NM.*c\.\d*)([ATCGatcg]+)(>None)", r"\1del\2", candidate)

    # TODO: Normalize multiple deletions and delins
    # TODO: Limit to only specific BRCA transcripts
    # ex: 23199084	NM_007294.3:c.2681AA>None|NM_007300.3:c.2681AA>None

    try:
        parsed_hgvs = parser.parse_hgvs_variant(candidate)
        try:
            return str(mapper.c_to_g(parsed_hgvs))
        except hgvs.exceptions.HGVSInvalidVariantError:
            print("Failed Mapping: (HGVSInvalidVariantError): {}".format(candidate))
        except hgvs.exceptions.HGVSInvalidIntervalError:
            print("Failed Mapping (HGVSInvalidIntervalError): {}".format(candidate))
        except hgvs.exceptions.HGVSDataNotAvailableError:
            print("Failed Mapping (HGVSDataNotAvailableError): {}".format(candidate))

    except hgvs.exceptions.HGVSParseError:
        print("Failed to parse: {}".format(candidate))

    return ""


def next_mention():
    for i, row in mentions.iterrows():
        matched = False
        norm_g_hgvs = ""

        for raw_hgvs in set([r.strip() for r in row.hgvsCoding.split("|")]):

            if not raw_hgvs:
                continue

            norm_g_hgvs = parse_and_map_hgvs(raw_hgvs)

            if not norm_g_hgvs:
                continue

            # normalized to normalized
            if norm_g_hgvs in variants:
                matched = True
                yield (variants[norm_g_hgvs].pyhgvs_Genomic_Coordinate_38,
                       row.docId, row.mutSnippets, 1)

            # normalized to synonym (BRCA Exchange synonyms replace : with .)
            for i, hit in variants.loc[variants.Synonyms.str.contains(
                    norm_g_hgvs.replace(":", "."), regex=False)].iterrows():
                matched = True
                yield (hit.pyhgvs_Genomic_Coordinate_38, row.docId, row.mutSnippets, 2)

        # texts to synonym
        # Note: Could always run but adds 40+ per variant...so only run if nothing else works
        if not matched:
            for text in set([t.strip() for t in row.texts.split("|")]):

                # Skip very short texts, i.e. M4N to reduce false positive
                if len(text) < 5:
                    continue

                for i, hit in variants[
                        variants.Synonyms.str.contains(text, regex=False)].iterrows():
                    # for i, hit in itertools.islice(
                    #     variants[variants.Synonyms.str.contains(
                    #         text, regex=False)].iterrows(), 10):
                    matched = True
                    yield (hit.pyhgvs_Genomic_Coordinate_38, row.docId, row.mutSnippets, 3)

        # if not matched:
        #     print("Failed to match: hgvsCoding={} Mapped={} Texts={}".format(
        #         raw_hgvs, norm_g_hgvs, row.texts))


if __name__ == "__main__":
    print("Connecting to hgvs server and mappers...")
    parser = hgvs.parser.Parser()
    mapper = hgvs.assemblymapper.AssemblyMapper(hgvs.dataproviders.uta.connect(),
                                                assembly_name="GRCh38")

    print("Loading variants...")
    if not os.path.exists("/crawl/variants-normalized.tsv"):
        variants = pd.read_csv("/crawl/output/release/built_with_change_types.tsv",
                               sep="\t", header=0, encoding="utf-8",
                               usecols=["pyhgvs_Genomic_Coordinate_38", "pyhgvs_cDNA", "Synonyms"])
        variants = variants.sort_values("pyhgvs_cDNA")

        print("Normalizing variants...")
        variants["norm_g_hgvs"] = variants["pyhgvs_cDNA"].apply(parse_and_map_hgvs)
        variants = variants.set_index("norm_g_hgvs", drop=True)
        variants.to_csv("/crawl/variants-normalized.tsv", sep="\t")
    variants = pd.read_csv("/crawl/variants-normalized.tsv",
                           sep="\t", header=0, encoding="utf-8", index_col="norm_g_hgvs")
    print("Found {} variants".format(variants.shape[0]))

    print("Loading mentions...")
    mentions = pd.read_csv("/crawl/mutations-trimmed.tsv",
                           sep="\t", header=0, encoding="utf-8", dtype="str")
    mentions = mentions.fillna("")
    mentions = mentions[mentions.mutSnippets != ""]
    mentions = mentions[(mentions.hgvsCoding != "") | (mentions.texts != "")]
    mentions = mentions.sort_values(["docId", "hgvsCoding"])
    print("Found {} mentions".format(mentions.shape[0]))

    print("Matching mentions...")
    matches = pd.DataFrame(
        [m for m in next_mention()],
        columns=["pyhgvs_Genomic_Coordinate_38", "pmid", "snippets", "score"]
    )
    matches = matches.set_index("pyhgvs_Genomic_Coordinate_38", drop=True)
    matches.to_csv("/crawl/mentions-matched.tsv", sep="\t")
