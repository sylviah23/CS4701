import requests
import json

URL = "https://query.wikidata.org/sparql"

ACTOR_QUERY = """
SELECT ?person ?personLabel ?genderLabel ?birthDate ?sitelinks ?occupationLabel WHERE {
  ?person wdt:P31 wd:Q5.
  ?person wdt:P106 wd:Q33999.  # actor
  OPTIONAL { ?person wdt:P21 ?gender. }
  OPTIONAL { ?person wdt:P569 ?birthDate. }

  ?person wikibase:sitelinks ?sitelinks.
  FILTER(?sitelinks > 100)

  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
LIMIT 200
"""

ATHLETE_QUERY = """
SELECT ?person ?personLabel ?genderLabel ?birthDate ?sitelinks WHERE {
  ?person wdt:P31 wd:Q5.
  ?person wdt:P106 wd:Q2066131.  # athlete
  OPTIONAL { ?person wdt:P21 ?gender. }
  OPTIONAL { ?person wdt:P569 ?birthDate. }
  
  ?person wikibase:sitelinks ?sitelinks.
  FILTER(?sitelinks > 50)

  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
LIMIT 200
"""

SINGER_QUERY = """
SELECT ?person ?personLabel ?genderLabel ?birthDate ?sitelinks WHERE {
  ?person wdt:P31 wd:Q5.
  ?person wdt:P106 wd:Q177220.  # singer
  OPTIONAL { ?person wdt:P21 ?gender. }
  OPTIONAL { ?person wdt:P569 ?birthDate. }
  
  ?person wikibase:sitelinks ?sitelinks.
  FILTER(?sitelinks > 50)

  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
LIMIT 200
"""

POLITICIAN_QUERY = """
SELECT ?person ?personLabel ?genderLabel ?birthDate ?sitelinks WHERE {
  ?person wdt:P31 wd:Q5.
  ?person wdt:P106 wd:Q82955.  # politician
  OPTIONAL { ?person wdt:P21 ?gender. }
  OPTIONAL { ?person wdt:P569 ?birthDate. }
  
  ?person wikibase:sitelinks ?sitelinks.
  FILTER(?sitelinks > 50)

  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
LIMIT 200
"""

SCIENTIST_QUERY = """
SELECT ?person ?personLabel ?genderLabel ?birthDate ?sitelinks WHERE {
  ?person wdt:P31 wd:Q5.
  ?person wdt:P106 wd:Q901.  # scientist
  OPTIONAL { ?person wdt:P21 ?gender. }
  OPTIONAL { ?person wdt:P569 ?birthDate. }

  ?person wikibase:sitelinks ?sitelinks.
  FILTER(?sitelinks > 50)

  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
LIMIT 200
"""

QUERIES = {
    "actor": ACTOR_QUERY,
    "athlete": ATHLETE_QUERY,
    "singer": SINGER_QUERY,
    "politician": POLITICIAN_QUERY,
    "scientist": SCIENTIST_QUERY
}

def fetch_data():
    headers = {
        "User-Agent": "CS4701AkinatorBot"
    }

    all_data = []

    for category, query in QUERIES.items():
      print(f"Fetching {category}s...")
      response = requests.get(
          URL,
          params={"query": query, "format": "json"},
          headers=headers
      )

      response.raise_for_status()
      data = response.json()
      for item in data["results"]["bindings"]:
        item["category"] = {"value": category}

      all_data.extend(data["results"]["bindings"])

    return all_data


def save_raw(data):
    with open("people.json", "w") as f:
        json.dump(data, f, indent=2)


if __name__ == "__main__":
    data = fetch_data()
    save_raw(data)

#For building secondary features after rounds of questioning
def extract_qid(dataset): 
   to_ret = {}

   for _, data in dataset.items(): 
      url = data["person"]["value"]
      qid = url.split("/")[-1]

      category = data.get("category", {}).get("value")

      to_ret[qid] = category 

   return to_ret 

def get_secondary_features(dataset):

    qids = extract_qid(dataset)

    if len(qids) < 30 or len(qids) > 300:
        return None

    values = " ".join(f"wd:{qid}" for qid in qids)

    feature_blocks = []

    # global features (always included)
    feature_blocks.append("?person wdt:P27 ?nationality.")
    feature_blocks.append("?person wdt:P19 ?birthPlace.")

    # category-specific features
    for qid, category in qids.items():

        if category == "actor":
            feature_blocks.append("?person wdt:P106 ?occupation.")
            feature_blocks.append("?person wdt:P136 ?genre.")

        elif category == "athlete":
            feature_blocks.append("?person wdt:P641 ?sport.")
            feature_blocks.append("?person wdt:P166 ?award.")
            feature_blocks.append("?person wdt:P54 ?team.")

        elif category == "singer":
            feature_blocks.append("?person wdt:P136 ?genre.")
            feature_blocks.append("?person wdt:P264 ?recordLabel.")
            feature_blocks.append("?person wdt:P1303 ?instrument.")

        elif category == "politician":
            feature_blocks.append("?person wdt:P39 ?positionHeld.")

        elif category == "scientist":
            feature_blocks.append("?person wdt:P101 ?field.")
            feature_blocks.append("?person wdt:P69 ?educatedAt.")
            feature_blocks.append("?person wdt:P166 ?award.")

    feature_block = "\n      OPTIONAL { " + " }\n      OPTIONAL { ".join(feature_blocks) + " }"

    return f"""
    SELECT ?person ?nationality ?birthCountry ?sport ?genre ?award ?team ?recordLabel ?instrument ?field ?educatedAt WHERE {{

      VALUES ?person {{
        {values}
      }}

      OPTIONAL {{ ?person wdt:P27 ?nationality. }}
      OPTIONAL {{
    ?person wdt:P19 ?birthPlace.
    ?birthPlace wdt:P17 ?birthCountry.
      }}



      {feature_block}

      SERVICE wikibase:label {{
        bd:serviceParam wikibase:language "en".
      }}
    }}
    """

