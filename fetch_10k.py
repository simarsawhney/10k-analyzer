"""
Day 1 script: pull a company's most recent 10-K filing from SEC EDGAR
and save the Risk Factors (Item 1A) and MD&A (Item 7) sections as plain text.

Before running:
1. pip install requests beautifulsoup4
2. Edit TICKER below to the company you picked
3. Edit USER_AGENT below — SEC requires a real name/email, it blocks generic requests
"""

import requests
from bs4 import BeautifulSoup
import re
import json

TICKER = "NKE"  # <-- change this to your chosen company
USER_AGENT = "Simar Sawhney sawhney.simar@gmail.com"  # <-- change this, SEC requires it

HEADERS = {"User-Agent": USER_AGENT}


def get_cik(ticker):
    """Look up a company's CIK number from its ticker."""
    url = "https://www.sec.gov/files/company_tickers.json"
    data = requests.get(url, headers=HEADERS).json()
    for entry in data.values():
        if entry["ticker"].upper() == ticker.upper():
            return str(entry["cik_str"]).zfill(10)
    raise ValueError(f"Ticker {ticker} not found")


def get_latest_10k_url(cik):
    """Find the most recent 10-K filing's document URL."""
    url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    data = requests.get(url, headers=HEADERS).json()
    recent = data["filings"]["recent"]

    for i, form in enumerate(recent["form"]):
        if form == "10-K":
            accession = recent["accessionNumber"][i].replace("-", "")
            primary_doc = recent["primaryDocument"][i]
            cik_int = int(cik)
            return f"https://www.sec.gov/Archives/edgar/data/{cik_int}/{accession}/{primary_doc}"

    raise ValueError("No 10-K found in recent filings")


def download_filing_text(doc_url):
    """Download the filing and strip HTML down to plain text."""
    resp = requests.get(doc_url, headers=HEADERS)
    soup = BeautifulSoup(resp.content, "html.parser")
    return soup.get_text(separator="\n")


def extract_section(full_text, start_pattern, end_pattern):
    """Pull the text between two Item headers using regex."""
    match = re.search(
        start_pattern + r"(.*?)" + end_pattern,
        full_text,
        re.DOTALL | re.IGNORECASE,
    )
    return match.group(1).strip() if match else "SECTION NOT FOUND — check patterns manually"


if __name__ == "__main__":
    print(f"Looking up CIK for {TICKER}...")
    cik = get_cik(TICKER)
    print(f"CIK: {cik}")

    print("Finding latest 10-K...")
    doc_url = get_latest_10k_url(cik)
    print(f"Filing URL: {doc_url}")

    print("Downloading and parsing filing (this can take a few seconds)...")
    full_text = download_filing_text(doc_url)

    # Risk Factors is usually Item 1A, ending at Item 1B or Item 2
    risk_factors = extract_section(
        full_text,
        r"Item\s+1A\.?\s*Risk Factors",
        r"Item\s+1B\.?\s*Unresolved Staff Comments|Item\s+2\.?\s*Properties",
    )

    # MD&A is usually Item 7, ending at Item 7A or Item 8
    mdna = extract_section(
        full_text,
        r"Item\s+7\.?\s*Management.?s Discussion",
        r"Item\s+7A\.?\s*Quantitative|Item\s+8\.?\s*Financial Statements",
    )

    with open(f"{TICKER}_risk_factors.txt", "w") as f:
        f.write(risk_factors)

    with open(f"{TICKER}_mdna.txt", "w") as f:
        f.write(mdna)

    print(f"\nSaved {TICKER}_risk_factors.txt and {TICKER}_mdna.txt")
    print("If either file says 'SECTION NOT FOUND', open the filing URL above")
    print("in a browser and check the exact wording of the section headers —")
    print("some filings format them slightly differently.")
