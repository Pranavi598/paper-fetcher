import requests
import csv
import argparse
import re
import time
from typing import List, Dict, Any, Optional, Tuple
from xml.etree import ElementTree as ET

BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
FETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

def fetch_pubmed_papers(query: str) -> List[Dict[str, Any]]:
    """Fetches research papers from PubMed based on a given query."""
    params = {
        "db": "pubmed",
        "term": query,
        "retmode": "json",
        "retmax": 10  # Limit results for demonstration purposes
    }
    try:
        response = requests.get(BASE_URL, params=params)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Failed to fetch PubMed data - {e}")
        return []

    # Log API Response
    with open("debug_output.txt", "w", encoding="utf-8") as debug_file:
        debug_file.write(response.text)

    print("Debug output saved to debug_output.txt")

    data = response.json()
    pmids = data.get("esearchresult", {}).get("idlist", [])
    return get_paper_details(pmids)


def is_non_academic(affiliation: str) -> bool:
    """Determines if an affiliation is non-academic."""
    academic_keywords = [
        "university", "institute", "college", "school", "department", "academy",
        "faculty", "centre for", "research center", "laboratory"
    ]
    return not any(keyword in affiliation.lower() for keyword in academic_keywords)


def get_paper_details(pmids: List[str]) -> List[Dict[str, Any]]:
    """Fetches paper details from PubMed given a list of PMIDs."""
    if not pmids:
        print("DEBUG: No PMIDs found!")
        return []

    params = {"db": "pubmed", "id": ",".join(pmids), "retmode": "xml"}

    try:
        response = requests.get(FETCH_URL, params=params)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Failed to fetch paper details - {e}")
        return []

    # Log API Response
    with open("debug_paper_details.txt", "w", encoding="utf-8") as debug_file:
        debug_file.write(response.text)

    print("DEBUG: Paper details saved to debug_paper_details.txt")

    root = ET.fromstring(response.content)
    return [parse_paper_data(article) for article in root.findall(".//PubmedArticle")]


def parse_paper_data(article: ET.Element) -> Dict[str, Any]:
    """Extracts relevant data from a PubMed paper entry."""
    title_elem = article.find(".//ArticleTitle")
    title = title_elem.text if title_elem is not None else "Unknown Title"

    return {
        "PubmedID": article.findtext(".//PMID", "N/A"),
        "Title": title,
        "Publication Date": extract_publication_date(article),
        "Non-academic Author(s)": process_author_data(article)[0],
        "Company Affiliation(s)": process_author_data(article)[1],
        "Corresponding Author Email": process_author_data(article)[2]
    }


def extract_publication_date(article: ET.Element) -> str:
    """Extracts and formats the publication date from the PubMed XML."""
    pub_date_elem = article.find(".//PubDate")
    if pub_date_elem is None:
        return "N/A"

    print(f"DEBUG: Extracting from PubDate -> {ET.tostring(pub_date_elem, encoding='unicode')}")

    year = pub_date_elem.findtext("Year", "N/A")
    month = pub_date_elem.findtext("Month", "N/A")
    day = pub_date_elem.findtext("Day", "N/A")

    if month != "N/A" and day != "N/A":
        return f"{year} {month} {day}"
    return year


def extract_author_name(author: ET.Element) -> Optional[str]:
    """Extracts the full name of an author from the XML data."""
    last_name = author.findtext("LastName", "").strip()
    fore_name = author.findtext("ForeName", "").strip()
    
    if last_name and fore_name:
        return f"{fore_name} {last_name}"
    elif last_name:
        return last_name
    return None


def process_author_data(article_data: ET.Element) -> Tuple[List[str], List[str], str]:
    """Processes author data to extract non-academic authors, affiliations, and email."""
    non_academic_authors, company_affiliations, email_list = [], set(), []

    author_list = article_data.find(".//AuthorList")
    if author_list is None:
        return ["N/A"], ["N/A"], "N/A"

    for author in author_list.findall("Author"):
        name = extract_author_name(author)
        if not name:
            continue

        for affiliation_info in author.findall(".//AffiliationInfo"):
            affiliation = affiliation_info.findtext("Affiliation", "").strip()
            if affiliation:
                # Extract valid email addresses
                email_matches = re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", affiliation)
                email_list.extend(email_matches)

                # Ensure it's a company and not an academic institution
                if is_non_academic(affiliation):
                    non_academic_authors.append(name)
                    company_affiliations.add(affiliation)

    corresponding_email = "; ".join(email_list) if email_list else "N/A"

    # Save extracted authors and affiliations for debugging
    with open("debug_extracted_authors.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Author", "Affiliation"])
        for author, affiliation in zip(non_academic_authors, company_affiliations):
            writer.writerow([author, affiliation])

    print("✅ Debug data saved to debug_extracted_authors.csv")

    return non_academic_authors or ["N/A"], list(company_affiliations) or ["N/A"], corresponding_email


def save_to_csv(papers: List[Dict[str, Any]], filename: str) -> None:
    """Saves paper data to a CSV file."""
    if not papers:
        print("No data available to save.")
        return

    try:
        with open(filename, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=papers[0].keys())
            writer.writeheader()
            writer.writerows(papers)
        print(f"✅ Results saved to {filename}")
    except PermissionError:
        print(f"ERROR: Cannot write to {filename} - Permission denied.")
    except Exception as e:
        print(f"ERROR: Failed to save data - {e}")


def main() -> None:
    """Main function to handle command-line arguments and execute the script."""
    parser = argparse.ArgumentParser(description="Fetch research papers from PubMed.")
    parser.add_argument("query", type=str, nargs="?", default="biotechnology", help="Search query for PubMed.")
    parser.add_argument("-f", "--file", type=str, help="Output CSV filename.")
    parser.add_argument("-d", "--debug", action="store_true", help="Enable debug mode.")
    args = parser.parse_args()

    papers = fetch_pubmed_papers(args.query)
    if not papers:
        print("ERROR: No papers found for the query.")
        return

    if args.file:
        save_to_csv(papers, args.file)
    else:
        for paper in papers:
            print("\n--- Paper ---")
            for key, value in paper.items():
                print(f"{key}: {value if not isinstance(value, list) else '; '.join(value)}")


if __name__ == "__main__":
    main()
