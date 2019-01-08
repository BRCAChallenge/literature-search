"""
Normalize LOVD truth into pmid plus list of normalized genomic hgvs
"""
import re
import pandas as pd

import hgvs.parser
import hgvs.dataproviders.uta
import hgvs.assemblymapper

if __name__ == "__main__":
    # Read in the lovd tables and add a transcript column
    brca1 = pd.read_table("tests/brca1LOVDTruthSet2017.tab", skiprows=1)
    brca1.rename(columns={c: c.split(" ")[1] for c in brca1.columns.values}, inplace=True)
    brca1["Variant/Transcript"] = "NM_007294.3"
    brca1["Variant/Chromosome"] = "chr17"

    brca2 = pd.read_table("tests/brca2LOVDTruthSet2017.tab", skiprows=1)
    brca2.rename(columns={c: c.split(" ")[1] for c in brca2.columns.values}, inplace=True)
    brca2["Variant/Transcript"] = "NM_000059.3"
    brca2["Variant/Chromosome"] = "chr13"

    variants = pd.concat([brca1, brca2], sort=False)

    # Extract pubmed id
    variants["pmid"] = variants["Variant/Reference"].str.extract(r"PMID(\d+)\:")
    variants = variants[~variants["pmid"].isnull()]

    # Normalize by mapping back to genomic coordinates
    parser = hgvs.parser.Parser()
    server = hgvs.dataproviders.uta.connect()
    mapper = hgvs.assemblymapper.AssemblyMapper(server, assembly_name="GRCh38")

    variants_normalized = pd.DataFrame(columns=["pmid", "norm_c_hgvs", "norm_g_hgvs"])

    for index, row in variants.iterrows():
        if row["Variant/DNA"].startswith("c."):
            candidate = row["Variant/Transcript"] + ":" + row["Variant/DNA"]
            try:
                norm_c_hgvs = parser.parse_hgvs_variant(candidate)
                norm_g_hgvs = mapper.c_to_g(norm_c_hgvs)
                pyhgvs_Genomic_Coordinate_38 = "{}:{}:{}".format(
                    row["Variant/Chromosome"],
                    *re.findall(r"(g\.[\d,_]*)(.*?)$", str(norm_g_hgvs))[0])
                print(row.pmid, norm_c_hgvs, norm_g_hgvs, pyhgvs_Genomic_Coordinate_38)
                variants_normalized = variants_normalized.append(
                    {"pmid": row.pmid,
                     "norm_c_hgvs": norm_c_hgvs,
                     "norm_g_hgvs": norm_g_hgvs,
                     "pyhgvs_Genomic_Coordinate_38": pyhgvs_Genomic_Coordinate_38},
                    ignore_index=True)
            except hgvs.exceptions.HGVSInvalidVariantError:
                print("Failed Mapping: HGVSInvalidVariantError")
            except hgvs.exceptions.HGVSInvalidIntervalError:
                print("Failed Mapping: HGVSInvalidIntervalError")
            except hgvs.exceptions.HGVSParseError:
                print("Failed Parsing")

    variants_normalized.to_csv("tests/lovd-normalized.tsv", sep="\t", index=False)
