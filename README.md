                                                                       Paper Fetcher

Paper Fetcher is a Python-based tool designed to fetch research papers from various sources. It helps automate the retrieval of academic papers based on given keywords or topics.

1.How the code is organized:
paper-fetcher
│── README.md                # Project documentation  
│── pyproject.toml            # Poetry configuration file  
│── poetry.lock                   # Dependency lock file  
│── <output/debug files>  # Generated output files (CSVs)  
│── paper_fetcher
    │── __init__.py                # Package initialization  
    │── fetch_papers.py        # Main script for fetching papers  
    │── __pycache__/            # Compiled Python files  
Root Directory (paper-fetcher/): Contains configuration files, documentation, and output files.
Main Module (paper_fetcher/): Contains the core functionality for fetching research papers.

2. Instructions on how to install dependencies and execute the program
Installation & Setup
Prerequisites
Python (Python 3.9.12 is installed)
Poetry (Poetry for dependency management)
i. Clone the Repository
git clone <repository_url>
cd paper-fetcher

ii. Install Dependencies
Using Poetry:
poetry install

iii.Run the Script
To fetch papers, execute:
poetry run paper_fetcher/fetch_papers.py

3.Tools & Libraries Used
This project utilizes the following tools and libraries:

LLM- https://chatgpt.com/
Python → https://www.python.org/
Poetry (Dependency management) → https://python-poetry.org/
Requests (HTTP requests) → https://docs.python-requests.org/
BeautifulSoup(Webscraping) →https://www.crummy.com/software/BeautifulSoup/
