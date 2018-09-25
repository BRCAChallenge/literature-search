import os
import unittest
import correlate

testdir = os.environ.get("TESTDIR")

expected_articles = {
    '30186769': {
        'vol': u'8',
        'abstract':
        u'In Ashkenazi Jewish (AJ) high risk families 3 mutations [2 in BRCA1 (c. 68_69del and c.5266dup) and 1 inBRCA2 (c.5946del)] account for the majority of high risk breast and ovarian cancer cases in that ethnic group. Few studies with limited number of genotyped individuals have expanded the spectrum of mutations in bothBRCA genes beyond the 3 mutation panel. In this study, 279 high risk individual AJ were counseled at CEMIC (Centro de Educaci\xf3n M\xe9dica e Investigaciones Cl\xednicas), and were genotyped first for the 3 recurrent mutation panel followed by Next Generation Sequencing (NGS) ofBRCA1 BRCA2 in 76 individuals who tested negative for the first genotyping step. Of 279 probands (259 women), 55 (50 women) harbored one of the 3 mutations (19.7%); Of 76 fully sequenced cases (73 women), 6 (5 women) (7.9%) carried a pathogenic mutation: inBRCA1, c.2728C>T - p.(Gln910*); c.5407-?_(*1_?)del and c.5445G>A - p.(Trp1815*); inBRCA2, c.5351dup - p.(Asn1784Lysfs*3); c.7308del - p.(Asn2436Lysfs*33) and c.9026_9030del - p.(Tyr3009Serfs*7). Of 61 mutation carriers the distribution was as follows: 11 cancer free at the time of genotyping, 34 female breast cancer cases with age range 28-72 years (41.6 \xb1 9.3), 3 male breast cancer cases with age range 59-75 years (65 \xb1 7.3), 6 breast and ovarian cancer cases with age range 35-60 years (breast 40.4 \xb1 5.2; ovary 47.8 \xb1 7.2) and 7 ovarian cancer cases with age range 41-77 years (60.6 \xb1 13.3). This information proved highly useful for counseling, treatment, and prevention for the patient and the family. In conclusion comprehensiveBRCA1/2 testing in AJ high risk breast ovarian cancer cases adds valuable clinically relevant information in a subset of cases estimated up to 7% and is therefore recommended.',
        'offset': 1506864983,
        'authorEmails': u'',
        'chunkId': u'0_00000',
        'year': 2018,
        'keywords': u'',
        'articleSection': u'',
        'fulltextUrl': u'https://www.frontiersin.org/articles/10.3389/fonc.2018.00323/full',
        'size': u'62825',
        'title': u'BRCA1 andBRCA2 Mutations Other Than the Founder Alleles Among Ashkenazi Jewish in the Population of Argentina.',
        'journalUniqueId': u'101568867',
        'source': u'',
        'externalId': u'PMID30186769',
        'articleType': u'research-article',
        'pmid': 30186769, 'issue': u'',
        'authorAffiliations': u'',
        'journal': u'Frontiers in oncology',
        'articleId': u'5030186769',
        'origFile': u'',
        'authors': u'Solano, Angela R; Liria, Natalia C; Jalil, Fernanda S; Faggionato, Daniela M; Mele, Pablo G; Mampel, Alejandra; Cardoso, Florencia C; Podesta, Ernesto J',
        'printIssn': u'2234-943X',
        'lang': u'eng',
        'publisher': u'Crawl',
        'doi': u'10.3389/fonc.2018.00323',
        'time': u'2018-09-15T00:14:59+0000',
        'eIssn': u'2234-943X',
        'page': u'323',
        'pmcId': 6113569
    },
    '23199084': {
        'vol': u'1',
        'abstract': u'Detection of mutations in hereditary breast and ovarian cancer-related BRCA1 and BRCA2 genes is an effective method of cancer prevention and early detection. Different ethnic and geographical regions have different BRCA1 and BRCA2 mutation spectrum and prevalence. Along with the emerging targeted therapy, demand and uptake for rapid BRCA1/2 mutations testing will increase in a near future. However, current patients selection and genetic testing strategies in most countries impose significant lag in this practice. The knowledge of the genetic structure of particular populations is important for the developing of effective screening protocol and may provide more efficient approach for the individualization of genetic testing. Elucidating of founder effect in BRCA1/2 genes can have an impact on the management of hereditary cancer families on a national and international healthcare system level, making genetic testing more affordable and cost-effective. The purpose of this review is to summarize current evidence about the BRCA1/2 founder mutations diversity in European populations.',
        'offset': 78, 'authorEmails': u'',
        'chunkId': u'0_00000',
        'year': 2010, 'keywords': u'',
        'articleSection': u'',
        'fulltextUrl': u'',
        'size': u'126825',
        'title': u'Founder BRCA1/2 mutations in the Europe: implications for hereditary breast-ovarian cancer prevention and control.',
        'journalUniqueId': u'101517307',
        'source': u'',
        'externalId': u'PMID23199084',
        'articleType': u'research-article',
        'pmid': 23199084, 'issue': u'3',
        'authorAffiliations': u'',
        'journal': u'The EPMA journal',
        'articleId': u'5023199084',
        'origFile': u'',
        'authors': u'Janavi\u010dius, Ram\u016bnas',
        'printIssn': u'1878-5077',
        'lang': u'eng',
        'publisher': u'Crawl',
        'doi': u'10.1007/s13167-010-0037-y',
        'time': u'2018-09-15T00:13:31+0000',
        'eIssn': u'1878-5077',
        'page': u'397',
        'pmcId': 3405339
    }
}

expected_variant_dict = {'NM_007294.3:c.5445G>A': 'chr17:43047665:C>T', 'NP_009225.1:p.Trp1815Ter': 'chr17:43047665:C>T', 'NM_000059.3:c.8327T>G': 'chr13:32363529:T>G', 'NM_007294.3:c.2359dupG': 'chr17:43093171:T>TC,chr17:g.43093172:C>CC', 'NP_009225.1:p.Glu787GlyfsTer3': 'chr17:43093171:T>TC,chr17:g.43093172:C>CC', 'NP_000050.2:p.Leu2776Ter': 'chr13:32363529:T>G'}

expected_matches = {'chr17:43093171:T>TC,chr17:g.43093172:C>CC': [{'hgvsRna': 'NM_007294.3:c.2590dupG|NM_007300.3:c.2590dupG|NM_007299.3:c.2552dupG|NM_007297.3:c.2639dupG', 'comment': '', 'isConfirmed': 'confirmed', 'mutSnippets': '[91] in a 49 BRCA1/2 positive families found six major recurrent founder mutations (three BRCA1 c.212+3A> (BIC: IVS5+3A>G),<<< c.2359dupG>>> (BIC: 2478insG), c.3661G>T (BIC: 3780G>T) and three BRCA2 c.516+1G>A (BIC: IVS6+1G>A), c.6275_6276delTT (BIC: 6503_6504delTT), c.8904delC (BIC: 9132d|BRCA1<<< c.2359dupG>>> and BRCA2 c.516+1G>A have not yet been reported in other populations.  ### The Netherlands (Holland)  Several founder mutations in BRCA1/2 have been identified in Holland [94], where significant regional and cultural differences exist.|   5272-1G>A    \xc2\xa0       Portuguese    \xc2\xa0  \xc2\xa0   c.156_157insAlu     384insAlu      Belgian     c.212+3A>G     IVS5+3A>G     c.516+1G>A     IVS6+1G>A     <<< c.2359dupG>>>     2478insG     c.6275_6276delTT     6503_6504delTT      c.3661G>T     3780G>T     c.8904delC     9132delC      Dutch     c.2685_2686delAA     2804d', 'geneType': 'entrez', 'hgvsProt': '', 'inDb': '', 'geneSymbol': 'BRCA1', 'end': '', 'geneSnippets': '', 'geneStarts': '', 'start': '', 'rsIdsMentioned': '', 'seqType': 'dna', 'mutStarts': '20413,20803,43784', 'docId': '23199084', 'varId': '23199084', 'mutPatNames': 'c.123dupA|c.123dupA|c.123dupA', 'offset': '', 'dbSnpEnds': '', 'chrom': '', 'hgvsCoding': 'NM_007294.3:c.2359dupG|NM_007300.3:c.2359dupG|NM_007299.3:c.2359dupG|NM_007297.3:c.2359dupG', 'geneEnds': '', 'texts': 'c.2359dupG| c.2359dupG', 'dbSnpSnippets': '', 'mutEnds': '20424,20814,43795', 'protId': '', 'dbSnpStarts': '', 'patType': 'dup', 'rsIds': 'rs397508964|rs397508964|na|na', 'entrezId': '672'}], 'chr17:43047665:C>T': [{'hgvsRna': 'NM_007294.3:c.5676G>A|NM_007300.3:c.5676G>A', 'comment': '', 'isConfirmed': 'confirmed', 'mutSnippets': '); Of 76 fully sequenced cases (73 women), 6 (5 women) (7.9%) carried a pathogenic mutation: in BRCA1, c.2728C>T - p.(Gln910*); c.5407-?_(*1_?)del and<<< c.5445G>A>>> - p.(Trp1815*); in BRCA2, c.5351dup - p.(Asn1784Lysfs*3); c.7308del - p.(Asn2436Lysfs*33) and c.9026_9030del - p.(Tyr3009Serfs*7).|(A) BRCA1 c.2728C>T - p.(Gln910*); (B) BRCA1 c.5407-?_(*1_?)del; (C) BRCA1:<<< c.5445G>A>>>-p.(Trp1815*); (D) BRCA2: c.5351dup - p.(Asn1784Lysfs*3); (E) BRCA2 c.7308del - p.(Asn2436Lysfs*33); (F) BRCA2 c.9026_9030del - p.(Tyr3009Serfs*7).  O|)   Total  73        Gene: Mutation  5  6.8      BRCA1: c.2728C>T - p.(Gln910*)  1    Ov (55)  0   BRCA1: c.5407-?_(*1_?)del  1    Br (37)  0   BRCA1:<<< c.5445G>A>>> - p.(Trp1815*)  1    Br (47)    BRCA2: c.7308del - p.(Asn2436Lysfs*33)  1    Br (38,45,47,52) & Ov (60, 64)  0   BRCA2: c.9026_9030del - p.(Tyr3009Se|The description of the mutations are in Table \xe2\x80\x8bTable4,4, as follows: BRCA1: c.2728C>T - p.(Gln910*), rs397509004, c.5407-?_(*1_?)del,<<< c.5445G>A>>> - p.(Trp1815*), rs397509284 and BRCA2: c.5351dup - p.(Asn1784Lysfs*3), rs80359508, c.7308del - p.(Asn2436Lysfs*33), c.9026_9030del - p.(Tyr3009Serfs*|  BRCA1:  <<< c.5445G>A>>> - p.(Trp1815*) rs397509284  This mutation is deposited by different laboratories at least 5 times at the LOVD.', 'geneType': 'entrez', 'hgvsProt': '', 'inDb': '', 'geneSymbol': 'BRCA1', 'end': '', 'geneSnippets': '', 'geneStarts': '', 'start': '', 'rsIdsMentioned': '', 'seqType': 'dna', 'mutStarts': '4898,15111,16945,18635,19549', 'docId': '30186769', 'varId': '30186769', 'mutPatNames': 'c.123T>A|c.123T>A|c.123T>A|c.123T>A|c.123T>A', 'offset': '', 'dbSnpEnds': '', 'chrom': '', 'hgvsCoding': 'NM_007294.3:c.5445G>A|NM_007300.3:c.5445G>A', 'geneEnds': '', 'texts': 'c.5445G>A| c.5445G>A', 'dbSnpSnippets': '', 'mutEnds': '4908,15121,16955,18645,19559', 'protId': '', 'dbSnpStarts': '', 'patType': 'sub', 'rsIds': 'rs397509284|rs397509275', 'entrezId': '672'}], 'chr13:32363529:T>G': [{'hgvsRna': 'NM_000059.3:c.8553T>G', 'comment': '', 'isConfirmed': 'confirmed', 'mutSnippets': 'equently.  The most recurrent mutation in BRCA2 is the Icelandic founder mutation c.771_775del5 (BIC: 999del5), three other (c.7480C>T (BIC: 7708C>T),<<< c.8327T>G>>> (BIC: 8555T>G), c.9118-2A>G (BIC: 9346-2A>G) and following (c. 6384del2 (BIC: 6503delTT), c.3853dupA (BIC: 4081insA) and c.5569G>T (BIC: 5797G>T)).|Some mutations are unique to the Finns, such as c.4096+3A>G (BIC: IVS11+3A>G) in BRCA1 and c.9117+1G>A (BIC: 9345+1G>A), c.7480C>T,<<< c.8327T>G>>> in BRCA2 genes.  The mutation spectrum in Eastern part slightly differs from those observed in the Northern and Southern parts of the country [139]. |sh     c.4097-2A>G     4216-2A>G     c.771_775del5     999del5      c.3485delA     3604delA     c.7480C>T     7708C>T      c.3626delT     3745delT    <<< c.8327T>G>>>     8555T>G      c.4327C>T     4446C>T     c.9118-2A>G     9346-2A>G      c.2684del2     2803delAA     c.9117+1G>A     9345+1G>A      c.5251C>T     5', 'geneType': 'entrez', 'hgvsProt': '', 'inDb': '', 'geneSymbol': 'BRCA2', 'end': '', 'geneSnippets': '', 'geneStarts': '', 'start': '', 'rsIdsMentioned': '', 'seqType': 'dna', 'mutStarts': '32943,33233,46217', 'docId': '23199084', 'varId': '23199084', 'mutPatNames': 'c.123T>A|c.123T>A|c.123T>A', 'offset': '', 'dbSnpEnds': '', 'chrom': '', 'hgvsCoding': 'NM_000059.3:c.8327T>G', 'geneEnds': '', 'texts': 'c.8327T>G| c.8327T>G', 'dbSnpSnippets': '', 'mutEnds': '32953,33243,46227', 'protId': '', 'dbSnpStarts': '', 'patType': 'sub', 'rsIds': 'rs397507977', 'entrezId': '675'}]}

expected_correlation_stats = {'duplicates': 3, 'notconfirmed': 93, 'novarid': 6, 'tried': 400, 'matched': 3}

# get_articles(article_file)
class test_get_articles(unittest.TestCase):
    def test_get_articles(self):
        article_dict = correlate.get_articles(testdir + "/articles.db")
        self.assertEqual(expected_articles, article_dict)


# get_known_variants(release_file)
class test_get_known_variants(unittest.TestCase):
    def test_get_known_variants(self):
        variant_dict = correlate.get_known_variants(testdir + "/built_with_change_types.tsv")
        self.assertEqual(expected_variant_dict, variant_dict)

# correlate_found_variants(found_file, built_pyhgvs)
class test_correlate_found_variants(unittest.TestCase):
    def test_correlate_found_variants(self):
        matches, correlation_stats = correlate.correlate_found_variants(testdir + "/foundMutations.tsv", expected_variant_dict)
        self.assertEqual(expected_matches, matches)
        self.assertEqual(expected_correlation_stats, correlation_stats)

#filter_articles(articles, matches)
class test_filter_articles(unittest.TestCase):
    def test_keep_all(self):
        articles, stats = correlate.filter_articles(expected_articles, expected_matches)
        self.assertEqual(expected_articles, articles)
        self.assertEqual({"noarticledata": 0}, stats)

    def test_filter_one(self):
        extra_articles = dict({"1234": {}}, **expected_articles)
        articles, stats = correlate.filter_articles(extra_articles, expected_matches)
        self.assertEqual(expected_articles, articles)
        self.assertEqual({"noarticledata": 0}, stats)

    def test_missing_one(self):
        missing_articles = dict(expected_articles)
        missing_articles.pop("23199084", None)
        articles, stats = correlate.filter_articles(missing_articles, expected_matches)
        self.assertEqual(missing_articles, articles)
        self.assertEqual({"noarticledata": 2}, stats)


if __name__ == '__main__':
    unittest.main()
