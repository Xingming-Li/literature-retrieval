import requests
import pandas as pd
import time

API_KEY = "961c10320fc700b1951232b622f6cdee"
BASE_URL = "https://api.elsevier.com/content/search/scopus"
HEADERS = {"X-ELS-APIKey": API_KEY, "Accept": "application/json"}

# Define query classes to split search safely
TECH_TERMS = [
    'Enter',
    'Query',
    'Classes',
    'Here'
]

def build_query(tech_term):
    """Builds each subquery string for Scopus (API-safe syntax)."""
    return (
        f'TITLE-ABS-KEY({tech_term}) '
        f'AND TITLE-ABS-KEY(sub1 OR sub2 OR sub3) '
        f'AND TITLE-ABS-KEY(sub4 OR sub5 OR sub6) '
        f'AND TITLE-ABS-KEY(sub7 OR sub8 OR sub9 OR sub10) '
        f'AND PUBYEAR > 2017'
    )

def fetch_articles(query, page_size=25, max_records=800):
    """Fetches Scopus results for one subquery."""
    print("Query:", query)

    all_articles = []
    seen_ids = set()

    for start in range(0, max_records, page_size):
        print(f"  Fetching records {start+1} to {start+page_size}...")
        params = {
            "query": query,
            "count": page_size,
            "start": start,
            "sort": "-citedby-count",
            "view": "STANDARD"
        }
        response = requests.get(BASE_URL, headers=HEADERS, params=params)
        if response.status_code != 200:
            print("  Error:", response.status_code, response.text)
            break

        entries = response.json().get("search-results", {}).get("entry", [])
        if not entries:
            break

        for entry in entries:
            eid = entry.get("eid", "N/A")
            if eid not in seen_ids:
                seen_ids.add(eid)
                all_articles.append({
                    "EID": eid,
                    "Title": entry.get("dc:title", "N/A"),
                    "Authors": entry.get("dc:creator", "N/A"),
                    "Year": entry.get("prism:coverDate", "N/A")[:4],
                    "Source": entry.get("prism:publicationName", "N/A"),
                    "DOI": entry.get("prism:doi", "N/A"),
                    "Citations": entry.get("citedby-count", "0"),
                    "Abstract": entry.get("dc:description", "N/A"),
                    "TechTerm": tech_term  # Track which subquery it came from
                })
        time.sleep(1)
    return all_articles


# --- Main execution block ---
all_results = []

for tech_term in TECH_TERMS:
    print(f"\n::: Fetching for subquery: {tech_term} :::")
    query = build_query(tech_term)
    results = fetch_articles(query)
    print(f"  --> Retrieved {len(results)} articles for {tech_term}")
    all_results.extend(results)

# --- Combine and clean up ---
df = pd.DataFrame(all_results)
df.drop_duplicates(subset=["EID"], inplace=True)
num_articles = len(df)
df.to_csv(f"scopus_{num_articles}.csv", index=False)

print(f"\n✅ Total Unique Articles Saved: {num_articles}")
print(f"Saved file: scopus_{num_articles}.csv")
