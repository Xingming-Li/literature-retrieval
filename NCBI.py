import requests
import xml.etree.ElementTree as ET
import pandas as pd
import time

BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
DB = "pubmed"

# Define query classes to split search safely
TECH_TERMS = [
    'Enter',
    'Query',
    'Classes',
    'Here'
]

def fetch_pubmed(term, retmax=800):
    # Build each subquery string
    query = f'("{term}") AND ("sub1" OR "sub2" OR "sub3") AND ("sub4" OR "sub5" OR "sub6") AND ("sub7" OR "sub8" OR "sub9" OR "sub10") AND ("2018"[Date - Publication] : "3000"[Date - Publication])'
    
    # Search phase: get PMIDs
    search = requests.get(BASE_URL + "esearch.fcgi", params={"db": DB, "term": query, "retmax": retmax, "retmode": "xml"})
    ids = [i.text for i in ET.fromstring(search.text).findall(".//Id")]
    print(f"🔹 Retrieved {len(ids)} PMIDs for term '{term}'")

    # Fetch phase: get article details
    all_records = []
    for i in range(0, len(ids), 50):  # fetch in batches
        chunk = ",".join(ids[i:i+50])
        fetch = requests.get(BASE_URL + "efetch.fcgi", params={"db": DB, "id": chunk, "retmode": "xml"})
        root = ET.fromstring(fetch.text)

        for article in root.findall(".//PubmedArticle"):
            pmid = article.findtext(".//PMID", "N/A")
            title = article.findtext(".//ArticleTitle", "N/A")
            year = article.findtext(".//PubDate/Year", "N/A")
            journal = article.findtext(".//Title", "N/A")
            abstract_parts = [a.text for a in article.findall(".//AbstractText") if a.text]
            abstract = " ".join(abstract_parts) if abstract_parts else "N/A"

            # Get DOI if present
            doi_elem = article.find(".//ELocationID[@EIdType='doi']")
            doi = doi_elem.text if doi_elem is not None else "N/A"

            # Extract authors
            authors = []
            for auth in article.findall(".//Author"):
                lastname = auth.findtext("LastName")
                forename = auth.findtext("ForeName")
                if lastname and forename:
                    authors.append(f"{forename} {lastname}")
            author_list = ", ".join(authors) if authors else "N/A"

            all_records.append({
                "EID": pmid,
                "Title": title,
                "Authors": author_list,
                "Year": year,
                "Source": journal,
                "DOI": doi,
                "Citations": "N/A",
                "Abstract": abstract,
                "TechTerm": term
            })
        time.sleep(0.5)
    return all_records


all_data = []
for term in TECH_TERMS:
    print(f"\n::: Fetching for subquery: {term} :::")
    data = fetch_pubmed(term)
    print(f"  --> Retrieved {len(data)} articles for {term}")
    all_data.extend(data)

df = pd.DataFrame(all_data)
df.drop_duplicates(subset=["EID"], inplace=True)
num_articles = len(df)
df.to_csv(f"pubmed_{num_articles}.csv", index=False)
print(f"\n✅ Total Unique Articles Saved: {num_articles}")
