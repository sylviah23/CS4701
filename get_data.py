import requests
import json

URL = "https://query.wikidata.org/sparql"

ACTOR_QUERY = """
SELECT ?person ?personLabel ?genderLabel ?birthDate WHERE {
  ?person wdt:P31 wd:Q5.
  ?person wdt:P106 wd:Q33999.  # actor
  OPTIONAL { ?person wdt:P21 ?gender. }
  OPTIONAL { ?person wdt:P569 ?birthDate. }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
LIMIT 100
"""

ATHLETE_QUERY = """
SELECT ?person ?personLabel ?genderLabel ?birthDate WHERE {
  ?person wdt:P31 wd:Q5.
  ?person wdt:P106 wd:Q2066131.  # athlete
  OPTIONAL { ?person wdt:P21 ?gender. }
  OPTIONAL { ?person wdt:P569 ?birthDate. }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
LIMIT 100
"""

SINGER_QUERY = """
SELECT ?person ?personLabel ?genderLabel ?birthDate WHERE {
  ?person wdt:P31 wd:Q5.
  ?person wdt:P106 wd:Q177220.  # singer
  OPTIONAL { ?person wdt:P21 ?gender. }
  OPTIONAL { ?person wdt:P569 ?birthDate. }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
LIMIT 100
"""

QUERIES = {
    "actor": ACTOR_QUERY,
    "athlete": ATHLETE_QUERY,
    "singer": SINGER_QUERY
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