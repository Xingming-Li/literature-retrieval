# OpenAlex Literature Retrieval

This script uses the [OpenAlex API](https://docs.openalex.org/api) to collect metadata about academic papers matching a given query, and exports the results to a CSV file.

## Features
- Query OpenAlex by topic and year
- Retrieve title, authors, publication source, abstract, and citations
- Handle pagination and deduplicate records

## Usage
```bash
pip install -r requirements.txt

```bash
python OpenAlexAPI.py
