import requests
import json
import time
import os

URL = "https://query.wikidata.org/sparql"

HEADERS = {
    "User-Agent": "CS4701AkinatorBot/1.0 (mm7swimmer@gmail.com)",
    "Accept": "application/sparql-results+json"
}

BATCH_SIZE = 25

OCCUPATION_QIDS = {
    "politician": "Q82955",
    "actor":      "Q33999",  
    "scientist":  "Q901",
    "athlete":    "Q2066131",
    "singer":     "Q177220",
    "musician":   "Q639669",
    "director":   "Q2526255",
    "author":     "Q36180",
    "comedian":   "Q245068",
}

SITELINK_MIN = 30

# Wikidata QIDs for gender
GENDERS = {
    "male":   "Q6581097",
    "female": "Q6581072",
}

# Wikidata QIDs for countries grouped by region
REGIONS = {
    "North_America": ["Q30", "Q16", "Q96"],
    "South_America": ["Q155", "Q414", "Q298"],
    "Europe":        ["Q145", "Q183", "Q142", "Q38", "Q29"],
    "Asia":          ["Q17", "Q148", "Q668", "Q796"],
    "Africa":        ["Q258", "Q79", "Q1049"],
    "Australia":     ["Q408"],
}

# Each filter combo is (category, gender, region)
FILTER_COMBOS = [
    (category, gender, region)
    for category in OCCUPATION_QIDS
    for gender in GENDERS
    for region in REGIONS
]

def make_query(occupation_qid, gender_qid, country_qids, limit, offset):
    country_values = ", ".join(f"wd:{q}" for q in country_qids)
    return f"""
SELECT ?person ?personLabel ?genderLabel ?birthDate ?sitelinks WHERE {{
  ?person wdt:P31 wd:Q5.
  ?person wdt:P106 wd:{occupation_qid}.
  ?person wdt:P21 wd:{gender_qid}.
  ?person wdt:P27 ?country.
  FILTER(?country IN ({country_values}))
  OPTIONAL {{ ?person wdt:P569 ?birthDate. }}
  
  ?person wikibase:sitelinks ?sitelinks.
  FILTER(?sitelinks > {SITELINK_MIN})

  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
}}
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
                timeout=30
            )
            if response.status_code == 429:
                wait = 2 ** attempt + 1
                print(f"  Rate limited (429). Sleeping {wait}s...")
                time.sleep(wait)
                continue
            if response.status_code == 504:
                print(f"  Gateway timeout. Sleeping 5s...")
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

def main():
    people, seen_qids = load_existing("people.json")
    print(f"Loaded {len(people)} existing people ({len(seen_qids)} unique QIDs)")

    TARGET = 4000
    total_added = 0

    for (category, gender, region) in FILTER_COMBOS:
        if len(people) >= TARGET:
            print(f"\nReached target of {TARGET} people. Done!")
            break

        occ_qid = OCCUPATION_QIDS[category]
        gender_qid = GENDERS[gender]
        country_qids = REGIONS[region]

        print(f"\n[{category} | {gender} | {region}]")

        offset = 0
        combo_added = 0

        while True:
            query = make_query(occ_qid, gender_qid, country_qids, BATCH_SIZE, offset)
            results = fetch_batch(query)

            if not results:
                break

            added = 0
            for item in results:
                qid = item["person"]["value"].split("/")[-1]
                if qid not in seen_qids:
                    item["category"] = {"value": category}
                    people.append(item)
                    seen_qids.add(qid)
                    added += 1

            combo_added += added
            total_added += added
            print(f"  offset={offset} → +{added} new (total: {len(people)})")

            if len(results) < BATCH_SIZE:
                break

            offset += BATCH_SIZE
            time.sleep(2.0)

        if combo_added > 0:
            save(people)
            print(f"  Saved. Total: {len(people)}")

        time.sleep(1.0)

    print(f"\nDone! Added {total_added} new people. Total: {len(people)}")

if __name__ == "__main__":
    main()