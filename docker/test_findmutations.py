import sys, os, unittest, mock
from os.path import *
sys.path.insert(0, join(dirname(abspath(__file__)), "../lib"))
import varFinder

testdir = os.environ.get("TESTDIR")

class test_pubFindMutations(unittest.TestCase):
    def setUp(self):
        varFinder.loadDb(logLevel=100)  # disable logging
        self.genes = [672, 675]         # BRCA1 and BRCA2 entrez ids

        self.c_variant_del_text = "The variant c.3616delG is pathogenic."
        self.c_variant_del_found = varFinder.findVariantDescriptions(self.c_variant_del_text, [])

        self.c_variant_sub_text = "We found that the variant c.135C>T may do some stuff."
        self.c_variant_sub_found = varFinder.findVariantDescriptions(self.c_variant_sub_text, [])

        self.c_variant_sub_offset_text = "We found that the variant c.135-563C>T may do some stuff."
        self.c_variant_sub_offset_found = varFinder.findVariantDescriptions(c_variant_sub_offset_text, [])

    def ground_variants(self, pmid, text, found):
        result = []

        for variant, mentions in found["dna"]+found["prot"]+found["intron"]:
            result.append(varFinder.groundVariant(pmid, text, variant, mentions, found["dbSnp"], self.genes, False))

        return result # array of tuples (grounded variants, ungrounded variants, beds)

    def test_c_variant_del_found(self):
        mutations = self.c_variant_del_found

        self.assertEqual(mutations["dbSnp"]+mutations["prot"]+mutations["intron"], [], \
                msg="Found unexpected non-cdna variants")
        self.assertNotEqual(len(mutations["dna"]), 0, msg="Did not find dna variant")
        self.assertEqual(len(mutations["dna"]), 1, msg="Found more than one dna variant (found {})".format(mutations["dna"]))
        mut = mutations["dna"][0][0]
        print mut
        self.assertEqual(mut.mutType, "del", msg="Incorrect mutation type (should be 'sub')")
        self.assertEqual(mut.seqType, "dna", msg="Incorrect sequence tpye (should be 'dna')")
        self.assertEqual(mut.start, 3616, msg="Incorrect start position")
        self.assertEqual(mut.end, 3617, msg="Incorrect end position")
        self.assertEqual(mut.offset, 0, msg="Found an offset where no offset was expected")
        self.assertEqual(mut.origSeq, "G", msg="Incorrect original sequence")
        self.assertEqual(mut.mutSeq, None, msg="Found an alternate sequence where none was expected")

    def test_c_variant_del_grounded(self):
        grounding_results = self.ground_variants("0001", self.c_variant_del_text, self.c_variant_del_found)

        self.assertEqual(len(grounding_results), 1, msg="Got more than one result set from grounding of variant")
        grounded_muts, ungrouded_muts, _ = grounding_results[0]
        self.assertEqual(len(grounded_muts), 2, msg="Expected 2 grounded variants, got {}".format(len(grounded_muts)))
        self.assertIsNone(ungrounded_muts, msg="Got ungrounded variants")
        self.assertEqual(grounded[0].mutSnippets, "The variant<<< c.3616delG>>> is pathogenic.", msg="Incorrect match text")
        self.assertEqual(grounded[0].geneSymbol, "BRCA1", msg="Incorrect gene")
        self.assertEqual(grounded[0].hgvsCoding, "NM_007294.3:c.3616delG|NM_007300.3:c.3616delG", msg="Incorrect hgvsCoding")
        self.assertEqual(grounded[1].mutSnippets, "The variant<<< c.3616delG>>> is pathogenic.", msg="Incorrect match text")
        self.assertEqual(grounded[0].geneSymbol, "BRCA2", msg="Incorrect gene")
        self.assertEqual(grounded[1].hgvsCoding, "NM_000059.3:c.3616delG", msg="Incorrect hgvsCoding")
        

    def test_c_variant_del_offset_found(self):  
        pass

    def test_c_variant_del_offset_grounded(self):  
        pass

    def test_c_variant_sub_found(self):
        mutations = selft.c_variant_sub_found

        self.assertEqual(mutations["dbSnp"]+mutations["prot"]+mutations["intron"], [], \
                msg="Found unexpected non-cdna variants")
        self.assertNotEqual(len(mutations["dna"]), 0, msg="Did not find dna variant")
        self.assertEqual(len(mutations["dna"]), 1, msg="Found more than one dna variant (found {})".format(mutations["dna"]))
        mut = mutations["dna"][0][0]
        self.assertEqual(mut.mutType, "sub", msg="Incorrect mutation type (should be 'sub')")
        self.assertEqual(mut.seqType, "dna", msg="Incorrect sequence tpye (should be 'dna')")
        self.assertEqual(mut.start, 135, msg="Incorrect start position")
        self.assertEqual(mut.end, 136, msg="Incorrect end position")
        self.assertEqual(mut.offset, 0, msg="Found an offset where no offset was expected")
        self.assertEqual(mut.origSeq, "C", msg="Incorrect original sequence")
        self.assertEqual(mut.mutSeq, "T", msg="Incorrect alternate sequence")

    def test_c_variant_sub_grounded(self):
        pass

    def test_c_variant_sub_offset_found(self):
        mutations = self.c_variant_sub_offset_found

        self.assertEqual(mutations["dbSnp"]+mutations["prot"]+mutations["intron"], [], \
                msg="Found unexpected non-cdna variants")
        self.assertNotEqual(len(mutations["dna"]), 0, msg="Did not find dna variant")
        # We currently get false positives for offsets ("c.123-10T>G" get both "c.123-10T>G" and "10T>G")
        # TODO: add @expectedFail tests for these false positives
        #self.assertEqual(len(mutations["dna"]), 1, msg="Found more than one dna variant (found {})".format(mutations["dna"]))
        mut = mutations["cdna"][0]
        self.assertEqual(mut.mutType, "sub", msg="Incorrect mutation type (should be 'sub')")
        self.assertEqual(mut.seqType, "dna", msg="Incorrect sequence tpye (shoudl be 'dna')")

    def test_c_variant_sub_offset_grounded(self):
        pass

    def test_c_variant_ins_found(self):
        pass

    def test_c_variant_ins_grounded(self):
        pass

    def test_c_variant_ins_offset_found(self):
        pass

    def test_c_variant_ins_offset_grounded(self):
        pass

    def test_c_variant_dup_found(self):
        pass

    def test_c_variant_dup_grounded(self):
        pass

    def test_c_variant_dup_offset_found(self):
        pass

    def test_c_variant_dup_offset_grounded(self):
        pass

if __name__ == '__main__':
    unittest.main()
