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
                r = requests.get(WIKIDATA_API, params=params, headers=headers, timeout=30)
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
                time.sleep(2 ** attempt)
                continue
            try:
                data = r.json()
            except Exception:
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
                entity.get("labels", {}).get("en", {}).get("value", qid)
            )
        time.sleep(0.3)
    return labels


def get_claim_qids(claims, property_id):
    """Extract all QIDs for a given property from claims."""
    result = []
    for claim in claims.get(property_id, []):
        try:
            result.append(claim["mainsnak"]["datavalue"]["value"]["id"])
        except:
            continue
    return result


def extract_nationalities(entities):
    nationality_map = {}
    for qid, entity in entities.items():
        claims = entity.get("claims", {})
        countries = get_claim_qids(claims, "P27")
        if countries:
            nationality_map[qid] = countries
    return nationality_map


def extract_awards(entities):
    """Extract award QIDs (P166) for each person."""
    award_map = {}
    for qid, entity in entities.items():
        claims = entity.get("claims", {})
        awards = get_claim_qids(claims, "P166")
        if awards:
            award_map[qid] = awards
    return award_map


def extract_sports(entities):
    """Extract sport QIDs (P641) for each person."""
    sport_map = {}
    for qid, entity in entities.items():
        claims = entity.get("claims", {})
        sports = get_claim_qids(claims, "P641")
        if sports:
            sport_map[qid] = sports
    return sport_map


def extract_instruments(entities):
    """Extract instrument QIDs (P1303) for each person."""
    instrument_map = {}
    for qid, entity in entities.items():
        claims = entity.get("claims", {})
        instruments = get_claim_qids(claims, "P1303")
        if instruments:
            instrument_map[qid] = instruments
    return instrument_map


def extract_positions(entities):
    """Extract position held QIDs (P39) for each person."""
    position_map = {}
    for qid, entity in entities.items():
        claims = entity.get("claims", {})
        positions = get_claim_qids(claims, "P39")
        if positions:
            position_map[qid] = positions
    return position_map


def extract_fields(entities):
    """Extract field of work QIDs (P101) for each person."""
    field_map = {}
    for qid, entity in entities.items():
        claims = entity.get("claims", {})
        fields = get_claim_qids(claims, "P101")
        if fields:
            field_map[qid] = fields
    return field_map


# Bucketing functions (QID label -> feature bucket)

AWARD_BUCKETS = {
    "won_oscar":   ["Academy Award", "Oscar"],
    "won_emmy":    ["Emmy"],
    "won_tony":    ["Tony Award"],
    "won_grammy":  ["Grammy"],
    "won_nobel":   ["Nobel"],
    "won_olympic": ["Olympic"],
}

SPORT_BUCKETS = {
    "plays_team_sport":   ["football", "basketball", "baseball", "cricket", "hockey", "rugby", "volleyball", "soccer"],
    "plays_racket_sport": ["tennis", "badminton", "table tennis", "squash"],
    "plays_combat_sport": ["boxing", "wrestling", "judo", "karate", "mixed martial arts"],
    "plays_racing_sport": ["formula one", "racing", "cycling", "motorsport"],
    "plays_water_sport":  ["swimming", "diving", "surfing", "water polo"],
    "plays_winter_sport": ["skiing", "snowboarding", "skating", "biathlon"],
    "plays_track_field":  ["athletics", "running", "marathon", "sprinting", "pole vault"],
    "plays_golf":         ["golf"],
    "plays_gymnastics":   ["gymnastics"],
}

INSTRUMENT_BUCKETS = {
    "plays_strings": ["guitar", "violin", "bass", "cello", "banjo", "ukulele", "harp"],
    "plays_keys":    ["piano", "keyboard", "organ", "synthesizer"],
    "plays_wind":    ["trumpet", "saxophone", "flute", "clarinet", "trombone"],
    "plays_percussion": ["drums", "percussion"],
    "plays_vocals":  ["voice", "vocals", "singing"],
}

POLITICIAN_BUCKETS = {
    "is_president":       ["president"],
    "is_prime_minister":  ["prime minister"],
    "is_senator_or_mp":   ["senator", "member of parliament", "representative", "congressman"],
    "is_governor":        ["governor"],
    "is_minister":        ["minister", "secretary of state", "chancellor"],
}

SCIENTIST_FIELD_BUCKETS = {
    "field_physical_science": ["physics", "chemistry", "astronomy", "mathematics", "geology"],
    "field_life_science":     ["biology", "medicine", "neuroscience", "genetics", "ecology"],
    "field_social_science":   ["psychology", "economics", "sociology", "political science", "anthropology"],
    "field_computer_science": ["computer science", "artificial intelligence", "engineering"],
}

def bucket_labels(labels, bucket_map):
    """Given a list of label strings and a bucket map, return which buckets apply."""
    result = {}
    labels_lower = [l.lower() for l in labels]
    for bucket, keywords in bucket_map.items():
        result[bucket] = 0
        for label in labels_lower:
            if any(kw in label for kw in keywords):
                result[bucket] = 1
                break
    return result


def enrich_people(people, nationality_map, award_buckets_map, sport_buckets_map,
                  instrument_buckets_map, position_buckets_map, field_buckets_map):
    for person in people:
        qid = extract_qid(person)
        category = person.get("category", {}).get("value", "")

        # Nationality (all categories)
        person["nationalities"] = nationality_map.get(qid, [])

        # Awards (actor, director, singer, musician, comedian, scientist)
        if category in ["actor", "director", "singer", "musician", "comedian", "scientist"]:
            awards = award_buckets_map.get(qid, {})
            person["award_features"] = awards

        # Sports (athlete)
        if category == "athlete":
            sports = sport_buckets_map.get(qid, {})
            person["sport_features"] = sports

        # Instruments (singer, musician)
        if category in ["singer", "musician"]:
            instruments = instrument_buckets_map.get(qid, {})
            person["instrument_features"] = instruments

        # Positions (politician)
        if category == "politician":
            positions = position_buckets_map.get(qid, {})
            person["position_features"] = positions

        # Fields (scientist)
        if category == "scientist":
            fields = field_buckets_map.get(qid, {})
            person["field_features"] = fields

    return people


def main():
    with open("people.json", "r", encoding="utf-8") as f:
        people = json.load(f)

    print(f"Loaded {len(people)} people")
    qids = [extract_qid(p) for p in people]

    print("Fetching Wikidata entities...")
    entities = fetch_entities(qids)
    print(f"Fetched {len(entities)} entities")

    # Nationalities
    print("\nExtracting nationalities...")
    nationality_map_qid = extract_nationalities(entities)
    all_country_qids = set()
    for qlist in nationality_map_qid.values():
        all_country_qids.update(qlist)
    print(f"Resolving {len(all_country_qids)} country labels...")
    time.sleep(2)
    country_labels = resolve_labels(list(all_country_qids))
    nationality_map = {
        person: [country_labels.get(c, c) for c in countries]
        for person, countries in nationality_map_qid.items()
    }
    print(f"Found nationalities for {len(nationality_map)} people")

    # Awards
    print("\nExtracting awards...")
    award_map_qid = extract_awards(entities)
    all_award_qids = set(q for qs in award_map_qid.values() for q in qs)
    print(f"Resolving {len(all_award_qids)} award labels...")
    time.sleep(2)
    award_labels = resolve_labels(list(all_award_qids))
    award_buckets_map = {
        qid: bucket_labels([award_labels.get(q, "") for q in qids], AWARD_BUCKETS)
        for qid, qids in award_map_qid.items()
    }

    # Sports
    print("\nExtracting sports...")
    sport_map_qid = extract_sports(entities)
    all_sport_qids = set(q for qs in sport_map_qid.values() for q in qs)
    print(f"Resolving {len(all_sport_qids)} sport labels...")
    time.sleep(2)
    sport_labels = resolve_labels(list(all_sport_qids))
    sport_buckets_map = {
        qid: bucket_labels([sport_labels.get(q, "") for q in qids], SPORT_BUCKETS)
        for qid, qids in sport_map_qid.items()
    }

    # Instruments
    print("\nExtracting instruments...")
    instrument_map_qid = extract_instruments(entities)
    all_instrument_qids = set(q for qs in instrument_map_qid.values() for q in qs)
    print(f"Resolving {len(all_instrument_qids)} instrument labels...")
    time.sleep(2)
    instrument_labels = resolve_labels(list(all_instrument_qids))
    instrument_buckets_map = {
        qid: bucket_labels([instrument_labels.get(q, "") for q in qids], INSTRUMENT_BUCKETS)
        for qid, qids in instrument_map_qid.items()
    }

    # Positions (politicians)
    print("\nExtracting positions...")
    position_map_qid = extract_positions(entities)
    all_position_qids = set(q for qs in position_map_qid.values() for q in qs)
    print(f"Resolving {len(all_position_qids)} position labels...")
    time.sleep(2)
    position_labels = resolve_labels(list(all_position_qids))
    position_buckets_map = {
        qid: bucket_labels([position_labels.get(q, "") for q in qids], POLITICIAN_BUCKETS)
        for qid, qids in position_map_qid.items()
    }

    # Fields (scientists)
    print("\nExtracting fields of work...")
    field_map_qid = extract_fields(entities)
    all_field_qids = set(q for qs in field_map_qid.values() for q in qs)
    print(f"Resolving {len(all_field_qids)} field labels...")
    time.sleep(2)
    field_labels = resolve_labels(list(all_field_qids))
    field_buckets_map = {
        qid: bucket_labels([field_labels.get(q, "") for q in qids], SCIENTIST_FIELD_BUCKETS)
        for qid, qids in field_map_qid.items()
    }

    # Enrich and save
    print("\nEnriching dataset...")
    enriched = enrich_people(
        people,
        nationality_map,
        award_buckets_map,
        sport_buckets_map,
        instrument_buckets_map,
        position_buckets_map,
        field_buckets_map,
    )

    with open("people_enriched.json", "w", encoding="utf-8") as f:
        json.dump(enriched, f, indent=2)
    print(f"Saved to people_enriched.json ({len(enriched)} people)")


if __name__ == "__main__":
    main()