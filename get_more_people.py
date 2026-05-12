import requests
import json
import time
import os

URL = "https://query.wikidata.org/sparql"

HEADERS = {
    "User-Agent": "CS4701AkinatorBot/1.0 (mm7swimmer@gmail.com)",
    "Accept": "application/sparql-results+json"
}

BATCH_SIZE = 50

OCCUPATION_QIDS = {
    "businessman":      "Q43845",
    "entrepreneur":     "Q131524",
    "architect":        "Q42973",
    "philosopher":      "Q4964182",
    "explorer":         "Q11900058",
    "inventor":         "Q205375",
    "journalist":       "Q1930187",
    "chef":             "Q3499072",
    "fashion_designer": "Q3501317",
    "activist":         "Q15253558",
    "monarch":          "Q116",
    "military_leader":  "Q189290",
    "painter":          "Q1028181",
    "mathematician":    "Q170790",
    "revolutionary":    "Q3242115",
    "theologian":       "Q1234713",
    "sculptor":         "Q1281618",
}

SITELINK_MIN = 50

def make_query(occupation_qid, alive, limit, offset):
    if alive:
        death_filter = "FILTER NOT EXISTS { ?person wdt:P570 ?deathDate. }"
    else:
        death_filter = "?person wdt:P570 ?deathDate."

    return f"""
SELECT ?person ?personLabel ?genderLabel ?birthDate ?sitelinks WHERE {{
  ?person wdt:P31 wd:Q5.
  ?person wdt:P106 wd:{occupation_qid}.
  {death_filter}
  OPTIONAL {{ ?person wdt:P21 ?gender. }}
  OPTIONAL {{ ?person wdt:P569 ?birthDate. }}

  ?person wikibase:sitelinks ?sitelinks.
  FILTER(?sitelinks > {SITELINK_MIN})

  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
}}
ORDER BY DESC(?sitelinks)
LIMIT {limit}
OFFSET {offset}
"""

def fetch_batch(query):
    for attempt in range(5):
        try:
            response = requests.get(
                URL,
                params={"query": query, "format": "json"},
                headers=HEADERS,
                timeout=40
            )
            if response.status_code == 429:
                wait = 2 ** attempt + 1
                print(f"  Rate limited (429). Sleeping {wait}s...")
                time.sleep(wait)
                continue
            if response.status_code in (502, 503, 504):
                print(f"  Server error {response.status_code}. Sleeping 5s...")
                time.sleep(5)
                continue
            response.raise_for_status()
            return response.json()["results"]["bindings"]
        except Exception as e:
            print(f"  Error on attempt {attempt + 1}: {e}")
            time.sleep(2 ** attempt)
    return []

def load_existing(path="people.json"):
    if not os.path.exists(path):
        return [], set()
    with open(path, "r", encoding="utf-8") as f:
        people = json.load(f)
    seen_qids = {p["person"]["value"].split("/")[-1] for p in people}
    return people, seen_qids

def save(people, path="people.json"):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(people, f, indent=2)

def fetch_category(category, occ_qid, alive, seen_qids, people, cap=75):
    label = "alive" if alive else "dead"
    print(f"\n[{category} | {label}]")
    offset = 0
    added_total = 0

    while added_total < cap:
        query = make_query(occ_qid, alive, BATCH_SIZE, offset)
        results = fetch_batch(query)

        if not results:
            break

        added = 0
        for item in results:
            qid = item["person"]["value"].split("/")[-1]
            if qid not in seen_qids:
                item["category"] = {"value": category}
                item["is_alive"] = 1 if alive else 0
                people.append(item)
                seen_qids.add(qid)
                added += 1

        added_total += added
        print(f"  offset={offset} → +{added} new (total: {len(people)})")

        if len(results) < BATCH_SIZE:
            break

        offset += BATCH_SIZE
        time.sleep(1.5)

    return added_total

def main():
    people, seen_qids = load_existing("people.json")
    print(f"Loaded {len(people)} existing people ({len(seen_qids)} unique QIDs)")

    total_added = 0

    for category, occ_qid in OCCUPATION_QIDS.items():
        # fetch alive people
        added = fetch_category(category, occ_qid, alive=True, seen_qids=seen_qids, people=people)
        total_added += added
        if added > 0:
            save(people)

        time.sleep(1.0)

        # fetch dead people
        added = fetch_category(category, occ_qid, alive=False, seen_qids=seen_qids, people=people)
        total_added += added
        if added > 0:
            save(people)

        time.sleep(1.0)

    print(f"\nDone! Added {total_added} new people. Total: {len(people)}")
    print("Now run get_secondary_data.py to enrich the new people.")

if __name__ == "__main__":
    main()