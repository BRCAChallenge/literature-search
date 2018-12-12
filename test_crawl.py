import sys, os, unittest, mock, subprocess
from os.path import *
sys.path.insert(0, abspath(join(dirname(abspath(__file__)), "../")))
print sys.path

testdir = os.environ.get("TESTDIR")

# "crawler" might be a better term than publisher, as pmc is not really (?) a publisher
papers = [
        #(pmid, publisher, md5)
        ("23199084", "springer", "19d913f0a7232a9afa26988af5a94143"),
        ("30186769", "frontiers", "32b5c58b230a9a53278d95981f1f391e"),
        ("29288066", "elsevier", "109809cd5e382143f63dc77dd1a4dbd6"),
        ("29316072", "wiley", "6de752fba2f564f1e08faf464d148a01"),
        ("29296529", "tandf", "78aedf172d9a0e4ef839407f4134fe02"),
        ("29108297", "pmc", "f59af95b5e76386502bf9757f6738125"),
        ]

possible_paper_files = [
        "/tmp/TestCrawl/files/{}.main.pdf",
        "/tmp/TestCrawl/files/{}.main.doc",
        "/tmp/TestCrawl/files/{}.main.docx",
        "/tmp/TestCrawl/files/{}.main.txt",
        ]


global setup_done
setup_done = False

class test_pubCrawl(unittest.TestCase):
    def setUp(self):
        # We only want this run once
        global setup_done
        if setup_done:
            return

        crawled_papers = {}
        pmids = reduce(lambda str, (pmid, _, _1): "{}{}\n".format(str, pmid), papers, "") 

        os.mkdir("/tmp/TestCrawl")
        with open("/tmp/TestCrawl/pmids.txt", "w") as pmids_txt:
           pmids_txt.write(pmids)

        subprocess.call("python ../pubCrawl2 /tmp/TestCrawl", shell=True)

        setup_done = True

    def stub(self, pub):
        for pmid, publisher, md5 in papers:
            if publisher == pub:
                paper_files = map(lambda f: f.format(pmid), possible_paper_files)
                paper_file = None
                for name in paper_files:
                    if isfile(name):
                        paper_file = name
                        break

                self.assertIsNotNone(paper_file, \
                    msg="Paper {} from publisher {} was not successfully crawled".format(pmid, publisher))

                result_md5 = subprocess.check_output("md5sum {}".format(paper_file), shell=True).split(" ")[0]
                self.assertEqual(result_md5, md5, \
                        msg="MD5 hash of paper {} from publisher {} does not match expected hash (got {})".format(pmid, publisher, result_md5))

    def test_springer(self):
        self.stub("springer")

    def test_elsevier(self):
        self.stub("elsevier")

    def test_frontiers(self):
        self.stub("frontiers")

    def test_pmc(self):
        self.stub("pmc")

    # Wiley and TandF both have perpetually changing metadata timestamps
    # To test these, we need to parse the metadata and make sure it checks out (pmid, title, etc)
    @unittest.expectedFailure
    def test_wiley(self):
        self.stub("wiley")

    @unittest.expectedFailure
    def test_tandf(self):
        self.stub("tandf")

if __name__ == '__main__':
    unittest.main()
