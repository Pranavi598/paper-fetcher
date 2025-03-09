import unittest
import xml.etree.ElementTree as ET
from paper_fetcher.fetch_papers import fetch_pubmed_papers, extract_publication_date


class TestPubMedFunctions(unittest.TestCase):

    def test_fetch_pubmed_papers(self):
        """Test if PubMed API returns a valid response."""
        papers = fetch_pubmed_papers("biotechnology")
        self.assertIsInstance(papers, list)  # Should return a list
        self.assertGreater(len(papers), 0)  # List should not be empty

    def test_extract_publication_date(self):
        """Test publication date extraction."""
        xml_string = """<PubmedArticle>
            <MedlineCitation>
                <Article>
                    <PubDate>
                        <Year>2023</Year>
                        <Month>Feb</Month>
                        <Day>15</Day>
                    </PubDate>
                </Article>
            </MedlineCitation>
        </PubmedArticle>"""

        root = ET.fromstring(xml_string)
        self.assertEqual(extract_publication_date(root), "2023 Feb 15")  # Expected output


if __name__ == "__main__":
    unittest.main()
