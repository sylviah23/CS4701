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


def extract_is_alive(entities):
    """Returns a dict of qid -> 1 (alive) or 0 (dead) based on P570 (date of death)."""
    result = {}
    for qid, entity in entities.items():
        claims = entity.get("claims", {})
        result[qid] = 0 if "P570" in claims else 1
    return result


# Bucketing functions (QID label -> feature bucket)

AWARD_BUCKETS = {
    "won_oscar":   ["academy award", "oscar"],
    "won_emmy":    ["emmy"],
    "won_tony":    ["tony award"],
    "won_grammy":  ["grammy"],
    "won_nobel":   ["nobel"],
    "won_olympic": ["olympic"],
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

def extract_occupations(entities):
    """Extract occupation QIDs (P106) for each person."""
    occupation_map = {}
    for qid, entity in entities.items():
        claims = entity.get("claims", {})
        occupations = get_claim_qids(claims, "P106")
        if occupations:
            occupation_map[qid] = occupations
    return occupation_map


# Maps occupation labels to our category buckets
OCCUPATION_BUCKETS = {
    "is_actor":           ["actor", "actress", "film actor", "voice actor"],
    "is_singer":          ["singer", "vocalist", "rapper", "recording artist"],
    "is_musician":        ["musician", "composer", "songwriter", "singer", "vocalist", "rapper", "instrumentalist", "conductor"],
    "is_athlete":         ["athlete", "footballer", "basketball player", "tennis player", "swimmer", "boxer", "cyclist", "sprinter", "cricketer"],
    "is_politician":      ["politician", "statesman", "diplomat"],
    "is_scientist":       ["scientist", "researcher", "physicist", "chemist", "biologist", "astronomer", "geologist"],
    "is_director":        ["film director", "television director", "director"],
    "is_author":          ["author", "writer", "novelist", "poet", "journalist", "playwright"],
    "is_comedian":        ["comedian", "humorist", "comic"],
    "is_businessman":     ["businessperson", "businessman", "businesswoman", "executive", "ceo", "entrepreneur"],
    "is_entrepreneur":    ["entrepreneur", "businessperson", "founder"],
    "is_architect":       ["architect"],
    "is_philosopher":     ["philosopher", "thinker"],
    "is_explorer":        ["explorer", "navigator", "adventurer"],
    "is_inventor":        ["inventor"],
    "is_journalist":      ["journalist", "reporter", "correspondent", "editor"],
    "is_chef":            ["chef", "cook"],
    "is_fashion_designer":["fashion designer", "couturier"],
    "is_activist":        ["activist", "social activist", "political activist"],
    "is_monarch":         ["monarch", "king", "queen", "emperor", "empress", "pharaoh", "sultan", "tsar"],
    "is_military_leader": ["military personnel", "general", "admiral", "military officer", "commander"],
    "is_painter":         ["painter", "artist", "visual artist"],
    "is_mathematician":   ["mathematician"],
    "is_revolutionary":   ["revolutionary", "resistance fighter"],
    "is_theologian":      ["theologian", "religious leader", "clergy", "bishop", "priest", "imam"],
    "is_sculptor":        ["sculptor"],
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
                  instrument_buckets_map, position_buckets_map, field_buckets_map,
                  is_alive_map, occupation_buckets_map):
    for person in people:
        qid = extract_qid(person)

        # is_alive
        if "is_alive" not in person:
            person["is_alive"] = is_alive_map.get(qid, None)

        # Nationality
        person["nationalities"] = nationality_map.get(qid, [])

        # Occupations — store full list so akinator can set multiple is_X flags
        person["occupation_features"] = occupation_buckets_map.get(qid, {})

        # Awards — give to everyone
        person["award_features"] = award_buckets_map.get(qid, {})

        # Sports — give to everyone (non-athletes will just have all 0s)
        person["sport_features"] = sport_buckets_map.get(qid, {})

        # Instruments — give to everyone
        person["instrument_features"] = instrument_buckets_map.get(qid, {})

        # Positions — give to everyone
        person["position_features"] = position_buckets_map.get(qid, {})

        # Fields — give to everyone
        person["field_features"] = field_buckets_map.get(qid, {})

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
        person_qid: bucket_labels([award_labels.get(aqid, "") for aqid in award_qids], AWARD_BUCKETS)
        for person_qid, award_qids in award_map_qid.items()
    }

    # Sports
    print("\nExtracting sports...")
    sport_map_qid = extract_sports(entities)
    all_sport_qids = set(q for qs in sport_map_qid.values() for q in qs)
    print(f"Resolving {len(all_sport_qids)} sport labels...")
    time.sleep(2)
    sport_labels = resolve_labels(list(all_sport_qids))
    sport_buckets_map = {
        person_qid: bucket_labels([sport_labels.get(sqid, "") for sqid in sport_qids], SPORT_BUCKETS)
        for person_qid, sport_qids in sport_map_qid.items()
    }

    # Instruments
    print("\nExtracting instruments...")
    instrument_map_qid = extract_instruments(entities)
    all_instrument_qids = set(q for qs in instrument_map_qid.values() for q in qs)
    print(f"Resolving {len(all_instrument_qids)} instrument labels...")
    time.sleep(2)
    instrument_labels = resolve_labels(list(all_instrument_qids))
    instrument_buckets_map = {
        person_qid: bucket_labels([instrument_labels.get(iqid, "") for iqid in inst_qids], INSTRUMENT_BUCKETS)
        for person_qid, inst_qids in instrument_map_qid.items()
    }

    # Positions (politicians)
    print("\nExtracting positions...")
    position_map_qid = extract_positions(entities)
    all_position_qids = set(q for qs in position_map_qid.values() for q in qs)
    print(f"Resolving {len(all_position_qids)} position labels...")
    time.sleep(2)
    position_labels = resolve_labels(list(all_position_qids))
    position_buckets_map = {
        person_qid: bucket_labels([position_labels.get(pqid, "") for pqid in pos_qids], POLITICIAN_BUCKETS)
        for person_qid, pos_qids in position_map_qid.items()
    }

    # Fields (scientists)
    print("\nExtracting fields of work...")
    field_map_qid = extract_fields(entities)
    all_field_qids = set(q for qs in field_map_qid.values() for q in qs)
    print(f"Resolving {len(all_field_qids)} field labels...")
    time.sleep(2)
    field_labels = resolve_labels(list(all_field_qids))
    field_buckets_map = {
        person_qid: bucket_labels([field_labels.get(fqid, "") for fqid in fld_qids], SCIENTIST_FIELD_BUCKETS)
        for person_qid, fld_qids in field_map_qid.items()
    }

    # Occupations
    print("\nExtracting occupations...")
    occupation_map_qid = extract_occupations(entities)
    all_occupation_qids = set(q for qs in occupation_map_qid.values() for q in qs)
    print(f"Resolving {len(all_occupation_qids)} occupation labels...")
    time.sleep(2)
    occupation_labels = resolve_labels(list(all_occupation_qids))
    occupation_buckets_map = {
        person_qid: bucket_labels([occupation_labels.get(oqid, "") for oqid in occ_qids], OCCUPATION_BUCKETS)
        for person_qid, occ_qids in occupation_map_qid.items()
    }

    # is_alive
    print("\nExtracting alive/dead status...")
    is_alive_map = extract_is_alive(entities)
    print(f"  Alive: {sum(v for v in is_alive_map.values())} | Dead: {sum(1-v for v in is_alive_map.values())}")

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
        is_alive_map,
        occupation_buckets_map,
    )

    with open("people_enriched.json", "w", encoding="utf-8") as f:
        json.dump(enriched, f, indent=2)
    print(f"Saved to people_enriched.json ({len(enriched)} people)")


if __name__ == "__main__":
    main()