import json
import requests
import time

WIKIDATA_API = "https://www.wikidata.org/w/api.php"

def chunk(lst, size=25):
    for i in range(0, len(lst), size):
        yield lst[i:i + size]


def extract_qid(person):
    return person["person"]["value"].split("/")[-1]


def fetch_entities(qids):
    all_entities = {}

    headers = {
        "User-Agent": "CS4701Bot/1.0 (student project: mm7swimmer@gmail.com)",
        "Accept": "application/json"
    }

    batches = list(chunk(qids, 25))
    total = len(batches)

    print(f"Total batches: {total}")

    for i, batch in enumerate(batches, start=1):

        print(f"[{i}/{total}] Fetching {len(batch)} entities...")
        params = {
            "action": "wbgetentities",
            "ids": "|".join(batch),
            "format": "json",
            "props": "claims"
        }
        success = False

        for attempt in range(6):
            try:
                r = requests.get(
                    WIKIDATA_API,
                    params=params,
                    headers=headers,
                    timeout=30
                )
            except Exception as e:
                print(f"Request error: {e}")
                time.sleep(2)
                continue

            if r.status_code == 200:
                success = True
                break

            if r.status_code == 429:
                wait = (2 ** attempt) + 0.5
                print(f"Rate limited (429). retry={attempt+1}, sleeping {wait:.2f}s")
                time.sleep(wait)
                continue

            print(f"  Bad status: {r.status_code}")
            print(f"  {r.text[:200]}")
            break

        if not success:
            print("  Skipping batch after retries")
            continue
        try:
            data = r.json()
        except Exception:
            print("  Non-JSON response (skipping batch)")
            continue

        entities = data.get("entities", {})
        all_entities.update(entities)

        print(f"  Got {len(entities)} entities (total: {len(all_entities)})")
        time.sleep(0.3)

    print(f"\nDone. Total entities fetched: {len(all_entities)}")

    return all_entities

def extract_nationalities(entities):
    nationality_map = {}

    for qid, entity in entities.items():
        claims = entity.get("claims", {})

        if "P27" not in claims:
            continue

        countries = []

        for claim in claims["P27"]:
            try:
                countries.append(
                    claim["mainsnak"]["datavalue"]["value"]["id"]
                )
            except:
                continue

        nationality_map[qid] = countries
    return nationality_map

def enrich_people(people, nationality_map):
    for person in people:
        qid = extract_qid(person)
        person["nationalities"] = nationality_map.get(qid, [])

    return people


def resolve_labels(qids):
    labels = {}
    headers = {
        "User-Agent": "CS4701Bot/1.0 (student project: mm7swimmer@gmail.com)",
        "Accept": "application/json"
    }

    for i in range(0, len(qids), 50):
        batch = qids[i:i+50]
        success = False
        for attempt in range(5):
            try:
                r = requests.get(
                    WIKIDATA_API,
                    params={
                        "action": "wbgetentities",
                        "ids": "|".join(batch),
                        "format": "json",
                        "props": "labels",
                        "languages": "en"
                    },
                    headers=headers,   
                    timeout=30
                )
            except Exception as e:
                print("Request error:", e)
                time.sleep(2)
                continue

            if r.status_code != 200:
                print(f"Bad status in label fetch: {r.status_code}")
                print(r.text[:200])
                time.sleep(2 ** attempt)
                continue

            try:
                data = r.json()
            except Exception:
                print("Non-JSON response in label fetch")
                print(r.text[:200])
                time.sleep(2 ** attempt)
                continue

            success = True
            break

        if not success:
            print(f"Skipping label batch {i}-{i+50}")
            continue

        entities = data.get("entities", {})

        for qid, entity in entities.items():
            if "missing" in entity:
                labels[qid] = qid
                continue
            labels[qid] = (
                entity.get("labels", {})
                      .get("en", {})
                      .get("value", qid)
            )
        time.sleep(0.3)
    return labels

def main():
    with open("people.json", "r", encoding="utf-8") as f:
        people = json.load(f)

    print(f"Loaded {len(people)} people")
    qids = [extract_qid(p) for p in people]

    print("Fetching Wikidata entities...")
    entities = fetch_entities(qids)
    print(f"Fetched {len(entities)} entities")

    print("Extracting nationalities...")
    nationality_map_qid = extract_nationalities(entities)

    time.sleep(5)

    all_country_qids = set()
    for qlist in nationality_map_qid.values():
        all_country_qids.update(qlist)
    print(f"Resolving {len(all_country_qids)} country labels...")
    qid_to_name = resolve_labels(list(all_country_qids))
    nationality_map = {
        person: [qid_to_name.get(c, c) for c in countries]
        for person, countries in nationality_map_qid.items()
    }

    print(f"Found nationalities for {len(nationality_map)} people")
    print("Enriching dataset...")
    enriched = enrich_people(people, nationality_map)

    with open("people_enriched.json", "w", encoding="utf-8") as f:
        json.dump(enriched, f, indent=2)
    print("Saved to people_enriched.json")


if __name__ == "__main__":
    main()