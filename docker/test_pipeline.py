import sys
import json

paper_ignore_keys = ["time"]

def diff_counts(results, expected):
    errs = []
    res_vc = results["variantCount"]
    exp_vc = expected["variantCount"]
    res_pc = results["paperCount"]
    exp_pc = expected["paperCount"]

    if res_vc > exp_vc:
        errs.append("Found more variants than expected (found {}, expected {})".format(res_vc, exp_vc))
    elif res_vc < exp_vc:
        errs.append("Found less variants than expected (found {}, expected {})".format(res_vc, exp_vc))

    if res_pc > exp_pc:
        errs.append("Found more papers than expected (found {}, expected {})".format(res_pc, exp_pc))
    elif res_pc < exp_pc:
        errs.append("Found less papers than expected (found {}, expected {})".format(res_pc, exp_pc))

    return errs

def diff_papers(results, expected):
    errs = []
    results_set = set(results.iterkeys())
    expected_set = set(expected.iterkeys())

    if len(results_set - expected_set):
        errs.append("Found unexpected papers {}".format(list(results_set - expected_set)))
    elif len(expected_set - results_set):
        errs.append("Missing expected papers {}".format(list(expected_set - results_set)))

    for pmid, results_paper in results.iteritems():
        if pmid in expected:
            expected_paper = expected[pmid]

            results_paper_set = set(results_paper.iterkeys())
            expected_paper_set = set(expected_paper.iterkeys())
            if len(results_paper_set - expected_paper_set):
                errs.append("Found unexpected fields in paper with PMID{}: {}".format(pmid, list(results_paper_set - expected_paper_set)))
            elif len(expected_paper_set - results_paper_set):
                errs.append("Missing expected fields in paper with PMID{}: {}".format(pmid, list(expected_paper_set - results_paper_set)))

            for key, value in results_paper.iteritems():
                if key not in paper_ignore_keys and key in expected_paper and value != expected_paper[key]:
                    errs.append("Found unexpected value for field '{}' in paper with PMID{}: Got \"{}\", Expected \"{}\"" \
                            .format(key, pmid, value, expected_paper[key]))

    return errs

def diff_variants(results, expected):
    errs = []
    results_set = set(results.iterkeys())
    expected_set = set(expected.iterkeys())

    if len(results_set - expected_set):
        errs.append("Found unexpected variants {}".format(list(results_set - expected_set)))
    elif len(expected_set - results_set):
        errs.append("Missing expected variants {}".format(list(expected_set - results_set)))

    for results_variant_name, results_variant in results.iteritems():
        if results_variant_name in expected:
            expected_variant = expected[results_variant_name]

            if len(results_variant) != len(expected_variant):
                errs.append("Found unexpected number of matches for variant '{}': Got {}, Expected {}. (Supressing further errors for this variant)" \
                        .format(results_variant_name, len(results_variant), len(expected_variant)))
            else:
                for results_match, expected_match in zip(results_variant, expected_variant):
                    results_match_set = set(results_match.iterkeys())
                    expected_match_set = set(expected_match.iterkeys())
                    results_match_text = "[missing]"
                    if "texts" in results_match:
                        results_match_text = results_match["texts"]
                    if len(results_match_set - expected_match_set):
                        errs.append("Found unexpected fields in match with text '{}' for variant '{}': {}" \
                                .format(results_match_text, results_variant_name, list(results_match_set - expected_match_set)))
                    elif len(expected_match_set - results_match_set):
                        errs.append("Missing expected fields in match with text '{}' for variant '{}': {}" \
                                .format(results_match_text, results_variant_name, list(expected_match_set - results_match_set)))

                    for key, value in results_match.iteritems():
                        if key in expected_match and value != expected_match[key]:
                            errs.append("Found unexpected value for field '{}' in match with text '{}' for variant '{}': Got \"{}\", Expected \"{}\"" \
                                    .format(key, results_match_text, results_variant_name, value, expected_match[key]))

    return errs

def diff_stats(results, expected):
    print results, expected
    errs = []
    for k, v in results.iteritems():
        if v != expected[k]:
            errs.append("Found unexpected value for correlation statistic '{}': Got {}, Expected {}".format(k, v, expected[k]))

    return errs

def main(args):
    print args
    results_file, expected_file = args
    errs = []
    with open(results_file) as results_file:
        results = json.load(results_file)
    with open(expected_file) as expected_file:
        expected = json.load(expected_file)
    errs.extend(diff_counts(results, expected))
    errs.extend(diff_papers(results["papers"], expected["papers"]))
    errs.extend(diff_variants(results["variants"], expected["variants"]))
    errs.extend(diff_stats(results["stats"], expected["stats"]))
    if len(errs):
        print "End to end pipeline test(s) failed:"
        for err in errs:
            print "\t{}".format(err)
        return 1
    else:
        print "End to end pipeline test passed"
        return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
