"""
Match variants found in papers to variants in BRCA Exchange
"""
import re
import pandas as pd
import hgvs.parser


def parse_hgvs(parser, candidate):
    assert candidate

    # Normalize single deletions: NM_007300.3:c.1100C>None -> NM_007300.3:c.1100delC
    candidate = re.sub(r"(NM.*c\.\d*)([ATCGatcg]+)(>None)", r"\1del\2", candidate)

    # TODO: Normalize multiple deletions and delins
    # TODO: Limit to only specific BRCA transcripts
    # ex: 23199084	NM_007294.3:c.2681AA>None|NM_007300.3:c.2681AA>None

    try:
        return str(parser.parse_hgvs_variant(candidate))
    except hgvs.exceptions.HGVSParseError:
        print("Failed to parse: {}".format(candidate))

    return ""


def next_mention(row, parser):
    matched = False
    parsed_c_hgvs = ""

    for raw_hgvs in set([r.strip() for r in row.hgvsCoding.split("|")]):

        if not raw_hgvs:
            continue

        parsed_c_hgvs = parse_hgvs(parser, raw_hgvs)

        if not parsed_c_hgvs:
            continue

        # Try parsed hgvsCoding to pyhgvs_cDNA
        hits = variants[variants.pyhgvs_cDNA.str.contains(parsed_c_hgvs)]
        assert hits.shape[0] <= 1
        if hits.shape[0]:
            matched = True
            yield (hits.iloc[0].pyhgvs_Genomic_Coordinate_38,
                   row.docId, row.mutSnippets, 10)

        # Try parsed hgvsCoding to synonym (BRCA Exchange synonyms replace : with .)
        for i, hit in variants.loc[variants.Synonyms.str.contains(
                parsed_c_hgvs.replace(":", "."), regex=False)].iterrows():
            matched = True
            yield (hit.pyhgvs_Genomic_Coordinate_38, row.docId, row.mutSnippets, 7)

    # Try texts to synonym
    # Note: Could always run but adds 40+ per variant...so only run if nothing else works
    if not matched:
        for text in set([t.strip() for t in row.texts.split("|")]):

            # Skip very short texts, i.e. M4N to reduce false positive
            if len(text) < 6:
                continue

            for i, hit in variants[
                    variants.Synonyms.str.contains(text, regex=False)].iterrows():
                matched = True
                # Longer matches score higher...
                yield (hit.pyhgvs_Genomic_Coordinate_38,
                       row.docId, row.mutSnippets, len(text) - 5)

    if not matched:
        print("Failed to match: hgvsCoding={} Mapped={} Texts={}".format(
            raw_hgvs, parsed_c_hgvs, row.texts))


if __name__ == "__main__":
    print("Creating HGVS parser...")
    parser = hgvs.parser.Parser()

    print("Loading variants...")
    variants = pd.read_csv("/crawl/output/release/built_with_change_types.tsv",
                           sep="\t", header=0, encoding="utf-8",
                           usecols=["pyhgvs_Genomic_Coordinate_38", "pyhgvs_cDNA", "Synonyms"])
    print("Found {} variants".format(variants.shape[0]))

    print("Loading mentions...")
    mentions = pd.read_csv("/crawl/mutations-trimmed.tsv",
                           sep="\t", header=0, encoding="utf-8", dtype="str")
    mentions = mentions.fillna("")
    mentions = mentions[mentions.mutSnippets != ""]
    mentions = mentions[(mentions.hgvsCoding != "") | (mentions.texts != "")]
    mentions = mentions.sort_values(["docId", "hgvsCoding"])
    print("Found {} mentions".format(mentions.shape[0]))

    hits = [m for _, row in mentions.iterrows() for m in next_mention(row, parser)]
    matches = pd.DataFrame(
        hits,
        columns=["pyhgvs_Genomic_Coordinate_38", "pmid", "snippets", "points"]
    )
    matches = matches.set_index("pyhgvs_Genomic_Coordinate_38", drop=True)
    matches.to_csv("/crawl/mentions-matched.tsv", sep="\t")
