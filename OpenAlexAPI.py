import requests
import pandas as pd
import time

BASE_URL = "https://api.openalex.org/works"

def build_query(base_query, year):
    """
    Build query parameters for a given base query and year.
    """
    return {
        "filter": f"title.search:{base_query},from_publication_date:{year}-01-01,to_publication_date:{year}-12-31",
        "per-page": 50,
    }

def reconstruct_abstract(inverted_index):
    """
    Reconstruct abstract text from OpenAlex inverted index format.
    """
    if not isinstance(inverted_index, dict):
        return None
    try:
        sorted_words = sorted(
            [(pos, word) for word, positions in inverted_index.items() for pos in positions]
        )
        abstract = " ".join([word for pos, word in sorted_words])
        return abstract
    except Exception:
        return None

def get_source(entry):
    """
    Safely extract the best available source name from multiple possible fields.
    Handles cases where nested dictionaries are None.
    """
    # Primary: host_venue.display_name
    host_venue = entry.get("host_venue") or {}
    source = host_venue.get("display_name")

    # Fallback 1: primary_location.source.display_name
    if not source:
        primary_location = entry.get("primary_location") or {}
        primary_source = primary_location.get("source") or {}
        source = primary_source.get("display_name")

    # Fallback 2: locations[0].source.display_name
    if not source and entry.get("locations"):
        first_loc = entry["locations"][0] or {}
        loc_source = first_loc.get("source") or {}
        source = loc_source.get("display_name")

    return source or "N/A"

def fetch_articles(base_query, year, max_per_year=1500):
    """
    Fetch articles from OpenAlex for a given query and year.
    """
    all_articles = []
    seen_ids = set()
    cursor = "*"
    total_fetched = 0

    while cursor and total_fetched < max_per_year:
        print(f"Fetching records {total_fetched+1} to {total_fetched+50} for {year}...")
        params = build_query(base_query, year)
        params["cursor"] = cursor

        response = requests.get(BASE_URL, params=params)
        if response.status_code != 200:
            print("Error:", response.status_code, response.text)
            break

        data = response.json()
        results = data.get("results", [])
        if not results:
            break

        for entry in results:
            work_id = entry.get("id")
            if work_id not in seen_ids:
                seen_ids.add(work_id)

                authors = ", ".join(
                    [a["author"]["display_name"] for a in entry.get("authorships", []) if a.get("author")]
                ) or "N/A"

                source = get_source(entry)
                abstract_text = reconstruct_abstract(entry.get("abstract_inverted_index"))

                all_articles.append({
                    "ID": work_id,
                    "Title": entry.get("title", "N/A"),
                    "Authors": authors,
                    "Year": entry.get("publication_year", "N/A"),
                    "Source": source,
                    "DOI": entry.get("doi", "N/A"),
                    "Citations": entry.get("cited_by_count", 0),
                    "Abstract": abstract_text or "N/A",
                    "URL": entry.get("primary_location", {}).get("landing_page_url", "N/A")
                })

        total_fetched += len(results)
        cursor = data.get("meta", {}).get("next_cursor")
        time.sleep(1)  # polite delay to avoid rate limits

    return all_articles


# === Main Execution ===
BASE_QUERY = "Enter your query here"

all_data = []
for year in range(2016, 2026):
    print(f"\n ::: Fetching Year: {year} ::: ")
    articles = fetch_articles(BASE_QUERY, year, max_per_year=1500)
    all_data.extend(articles)

df = pd.DataFrame(all_data)
df.drop_duplicates(subset=["ID"], inplace=True)

updated_name = BASE_QUERY.replace(" ", "_")
output_filename = f"{updated_name}.csv"
df.to_csv(output_filename, index=False, encoding="utf-8-sig")

print(f"\n✅ Total Unique Articles Saved: {len(df)}")
print(f"📄 Saved to: {output_filename}")
