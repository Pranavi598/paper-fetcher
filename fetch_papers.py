import requests
import csv
import argparse
import re
from typing import List, Dict, Any

def fetch_pubmed_papers(query: str) -> List[Dict[str, Any]]:
    """Fetches research papers from PubMed based on a given query."""
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    params = {
        "db": "pubmed",
        "term": query,
        "retmode": "json",
        "retmax": 10  # Limit results for demonstration purposes
    }
    response = requests.get(base_url, params=params)
    response.raise_for_status()
    data = response.json()
    pmids = data.get("esearchresult", {}).get("idlist", [])
    return get_paper_details(pmids)

def get_paper_details(pmids: List[str]) -> List[Dict[str, Any]]:
    """Fetches paper details from PubMed given a list of PMIDs."""
    details_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
    params = {
        "db": "pubmed",
        "id": ",".join(pmids),
        "retmode": "json"
    }
    response = requests.get(details_url, params=params)
    response.raise_for_status()
    data = response.json().get("result", {})
    return [parse_paper_data(data[pmid]) for pmid in pmids if pmid in data]

def parse_paper_data(paper: Dict[str, Any]) -> Dict[str, Any]:
    """Extracts relevant data from a PubMed paper entry."""
    return {
        "PubmedID": paper.get("uid", "N/A"),
        "Title": paper.get("title", "N/A"),
        "Publication Date": paper.get("pubdate", "N/A"),
        "Non-academic Author(s)": find_non_academic_authors(paper),
        "Company Affiliation(s)": find_company_affiliations(paper),
        "Corresponding Author Email": extract_corresponding_author_email(paper)
    }

def find_non_academic_authors(paper: Dict[str, Any]) -> List[str]:
    """Identifies non-academic authors from author affiliations."""
    authors = paper.get("authors", [])
    return [author.get("name", "") for author in authors if is_non_academic(author)]

def find_company_affiliations(paper: Dict[str, Any]) -> List[str]:
    """Extracts company names from author affiliations."""
    return [author.get("affiliation", "") for author in paper.get("authors", []) if is_non_academic(author)]

def is_non_academic(author: Dict[str, Any]) -> bool:
    """Determines if an author is affiliated with a company based on heuristic rules."""
    affiliation = author.get("affiliation", "").lower()
    return any(keyword in affiliation for keyword in ["pharma", "biotech", "inc.", "ltd.", "corporation", "gmbh"])

def extract_corresponding_author_email(paper: Dict[str, Any]) -> str:
    """Extracts the corresponding author's email from the paper data."""
    email_match = re.search(r"[\w\.-]+@[\w\.-]+", paper.get("correspondence", ""))
    return email_match.group(0) if email_match else "N/A"

def save_to_csv(papers: List[Dict[str, Any]], filename: str) -> None:
    """Saves paper data to a CSV file."""
    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=papers[0].keys())
        writer.writeheader()
        writer.writerows(papers)

def main():
    parser = argparse.ArgumentParser(description="Fetch research papers from PubMed.")
    parser.add_argument("query", type=str, help="Search query for PubMed.")
    parser.add_argument("-f", "--file", type=str, help="Output CSV filename.")
    parser.add_argument("-d", "--debug", action="store_true", help="Enable debug mode.")
    args = parser.parse_args()

    papers = fetch_pubmed_papers(args.query)
    
    if args.debug:
        print("Fetched papers:", papers)
    
    if args.file:
        save_to_csv(papers, args.file)
        print(f"Results saved to {args.file}")
    else:
        for paper in papers:
            print(paper)

if __name__ == "__main__":
    main()

