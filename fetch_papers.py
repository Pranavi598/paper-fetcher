import requests
import csv
import argparse
import re
from typing import List, Dict, Any, Optional
from xml.etree import ElementTree as ET

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
    
    # Log API Response to a file
    with open("debug_output.txt", "w", encoding="utf-8") as debug_file:
        debug_file.write(response.text)
    
    print("Debug output saved to debug_output.txt")  # Inform user
    
    response.raise_for_status()
    data = response.json()
    pmids = data.get("esearchresult", {}).get("idlist", [])
    return get_paper_details(pmids)


def get_paper_details(pmids: List[str]) -> List[Dict[str, Any]]:
    """Fetches paper details from PubMed given a list of PMIDs."""
    if not pmids:
        print("DEBUG: No PMIDs found!")
        return []

    details_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    params = {
        "db": "pubmed",
        "id": ",".join(pmids),
        "retmode": "xml"
    }
    response = requests.get(details_url, params=params)
    
    # Log API Response
    with open("debug_paper_details.txt", "w", encoding="utf-8") as debug_file:
        debug_file.write(response.text)
    
    print("DEBUG: Paper details saved to debug_paper_details.txt")
    
    response.raise_for_status()
    root = ET.fromstring(response.content)
    
    papers = []
    for article in root.findall(".//PubmedArticle"):
        paper = parse_paper_data(article)
        papers.append(paper)
    
    return papers


def parse_paper_data(article: ET.Element) -> Dict[str, Any]:
    """Extracts relevant data from a PubMed paper entry."""
    # Extract article metadata
    article_data = article.find(".//Article")
    if article_data is None:
        return create_empty_paper_dict()
    
    # Extract PMID
    pmid = article.findtext(".//PMID", "N/A")
    
    # Extract title
    title = article_data.findtext(".//ArticleTitle", "N/A")
    
    # Extract publication date
    pub_date = extract_publication_date(article_data)
    
    # Process author and affiliation data
    authors, affiliations, email = process_author_data(article_data)
    
    return {
        "PubmedID": pmid,
        "Title": title,
        "Publication Date": pub_date,
        "Non-academic Author(s)": authors,
        "Company Affiliation(s)": affiliations,
        "Corresponding Author Email": email
    }


def create_empty_paper_dict() -> Dict[str, Any]:
    """Creates an empty paper dictionary with default values."""
    return {
        "PubmedID": "N/A",
        "Title": "N/A",
        "Publication Date": "N/A",
        "Non-academic Author(s)": [],
        "Company Affiliation(s)": [],
        "Corresponding Author Email": "N/A"
    }


def extract_publication_date(article_data: ET.Element) -> str:
    """Extracts and formats the publication date."""
    # Try to get the electronic publication date first
    pub_date_elem = article_data.find(".//PubDate") or article_data.find(".//PublicationDate")
    
    if pub_date_elem is None:
        return "N/A"
    
    year = pub_date_elem.findtext("Year", "N/A")
    month = pub_date_elem.findtext("Month", "N/A")
    day = pub_date_elem.findtext("Day", "N/A")
    
    if year != "N/A":
        if month != "N/A" and day != "N/A":
            return f"{year} {month} {day}"
        elif month != "N/A":
            return f"{year} {month}"
        else:
            return year
    
    return "N/A"


def is_non_academic(affiliation: str) -> bool:
    """
    Determines if an affiliation is non-academic based on enhanced heuristic rules.
    Returns True if the affiliation appears to be from industry or research center.
    """
    # Expanded list of corporate keywords
    corporate_keywords = [
        "pharma", "biotech", "inc", "ltd", "corporation", "corp", 
        "gmbh", "llc", "co.", "company", "industries", "therapeutics",
        "labs", "laboratories", "research centre", "research center", 
        "technologies", "bioscience", "genomics", "diagnostics", 
        "biopharm", "holdings", "division"
    ]
    
    # Expanded list of academic keywords to exclude
    academic_keywords = [
        "university", "college", "school of", "faculty of",
        "department of", "academy"
    ]
    
    affiliation_lower = affiliation.lower()
    
    # Check if it contains corporate keywords and doesn't contain academic keywords
    has_corporate = any(keyword in affiliation_lower for keyword in corporate_keywords)
    has_academic = any(keyword in affiliation_lower for keyword in academic_keywords)
    
    # Special case for research centers that aren't universities
    is_research_center = ("research" in affiliation_lower and not has_academic)
    
    return has_corporate or is_research_center


def process_author_data(article_data: ET.Element) -> tuple:
    """Processes author data to extract non-academic authors, affiliations, and email."""
    non_academic_authors = []
    company_affiliations = set()
    corresponding_email = "N/A"
    
    # Get all author lists - modern PubMed XML has different structures
    author_list = article_data.find(".//AuthorList")
    if author_list is None:
        return ["N/A"], ["N/A"], "N/A"
    
    # Process each author
    for author in author_list.findall("Author"):
        name = extract_author_name(author)
        if not name:
            continue
            
        # Extract affiliation information - handle both modern and legacy XML structures
        affiliations = []
        
        # Modern XML structure with AffiliationInfo elements
        for affiliation_info in author.findall(".//AffiliationInfo"):
            affiliation_text = affiliation_info.findtext("Affiliation", "").strip()
            if affiliation_text:
                affiliations.append(affiliation_text)
        
        # Legacy XML structure with direct Affiliation element
        direct_affiliation = author.findtext("Affiliation", "").strip()
        if direct_affiliation and not affiliations:
            affiliations.append(direct_affiliation)
        
        # Process affiliations for this author
        for affiliation in affiliations:
            # Check for email in affiliation
            email_match = re.search(r"[\w\.-]+@[\w\.-]+", affiliation)
            if email_match and corresponding_email == "N/A":
                corresponding_email = email_match.group(0)
            
            # Check if non-academic
            if is_non_academic(affiliation):
                non_academic_authors.append(name)
                company_affiliations.add(affiliation)
    
    # Format the results
    non_academic_authors = non_academic_authors if non_academic_authors else ["N/A"]
    company_affiliations_list = list(company_affiliations) if company_affiliations else ["N/A"]
    
    return non_academic_authors, company_affiliations_list, corresponding_email


def extract_author_name(author: ET.Element) -> str:
    """Extracts the full name of an author."""
    last_name = author.findtext("LastName", "").strip()
    fore_name = author.findtext("ForeName", "").strip()
    
    if not last_name and not fore_name:
        # Try collective name for group authors
        collective_name = author.findtext("CollectiveName", "").strip()
        if collective_name:
            return collective_name
        return ""
    
    return f"{last_name}, {fore_name}" if fore_name else last_name


def save_to_csv(papers: List[Dict[str, Any]], filename: str) -> None:
    """Saves paper data to a CSV file."""
    if not papers:
        print("No data available to save.")
        return
    
    try:
        with open(filename, mode="w", newline="", encoding="utf-8") as file:
            # Convert list fields to strings for CSV writing
            processed_papers = []
            for paper in papers:
                processed_paper = paper.copy()
                for key, value in processed_paper.items():
                    if isinstance(value, list):
                        processed_paper[key] = "; ".join(str(item) for item in value)
                processed_papers.append(processed_paper)
            
            writer = csv.DictWriter(file, fieldnames=papers[0].keys())
            writer.writeheader()
            writer.writerows(processed_papers)
        print(f"✅ Results saved to {filename}")
    except PermissionError:
        print(f"ERROR: Cannot write to {filename} - Permission denied. File may be open in another program.")
        # Try with a different filename
        alt_filename = f"pubmed_results_{int(time.time())}.csv"
        print(f"Trying alternative filename: {alt_filename}")
        save_to_csv(papers, alt_filename)
    except Exception as e:
        print(f"ERROR: Failed to save data - {e}")


def main():
    parser = argparse.ArgumentParser(description="Fetch research papers from PubMed.")
    parser.add_argument("query", type=str, nargs="?", default="biotechnology", help="Search query for PubMed.")
    parser.add_argument("-f", "--file", type=str, help="Output CSV filename.")
    parser.add_argument("-d", "--debug", action="store_true", help="Enable debug mode.")
    args = parser.parse_args()

    try:
        papers = fetch_pubmed_papers(args.query)
        if not papers:
            print("ERROR: No papers found for the query.")
            return
    except Exception as e:
        print(f"ERROR: Failed to fetch data - {e}")
        return
    
    if args.debug:
        print("Fetched papers:", papers)
    
    if args.file:
        save_to_csv(papers, args.file)
        print(f"✅ Results saved to {args.file}")
    else:
        for paper in papers:
            print("\n--- Paper ---")
            for key, value in paper.items():
                if isinstance(value, list):
                    print(f"{key}: {'; '.join(str(item) for item in value)}")
                else:
                    print(f"{key}: {value}")


if __name__ == "__main__":
    main()