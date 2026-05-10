import requests
import json
from collections import defaultdict

URL = "https://query.wikidata.org/sparql"

ACTOR_QUERY = """
SELECT ?person ?personLabel ?genderLabel ?birthDate ?sitelinks WHERE {
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
LIMIT 75
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
LIMIT 75
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
        "User-Agent": "CS4701AkinatorBot",
        "Accept": "application/sparql-results+json"
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
      qid = data.get("qid")


      for category in ["actor", "athlete", "singer", "politician", "scientist"]:
        if data.get(f"is_{category}") == 1:
           to_ret[qid] = category
           break
          
   return to_ret 

# for category in ["actor", "athlete", "singer", "politician", "scientist"]:
#          

def group(query, feature):
    group = defaultdict(set)

    for person in query: 
        name = person["person"]["value"].split("/")[-1]
        if f"{feature}Label" in person:
            extract = person[f"{feature}Label"]["value"]
            group[name].add(extract)
    
    return {k: ",".join(sorted(v)) for k, v in group.items()}

def secondary_trial_nat(dataset):
    qids = extract_qid(dataset)

    if len(qids) < 30 or len(qids) > 300:
        return None

    values = " ".join(f"wd:{qid}" for qid in qids)

    query = f"""
    SELECT ?person ?nationalityLabel WHERE {{
      VALUES ?person {{
        {values}
      }}

      ?person wdt:P27 ?nationality.

      SERVICE wikibase:label {{
        bd:serviceParam wikibase:language "en".
      }}
    }}
    """
    print("querying done")
    return query

def get_nationality_trial(dataset):
    headers = {
        "User-Agent": "CS4701AkinatorBot/1.0",
        "Accept": "application/sparql-results+json"
    }

    query = secondary_trial_nat(dataset)
    if query is None:
        return None

    response = requests.post(
        URL,
        data={"query": query, "format": "json"},
        headers=headers
    )

    response.raise_for_status()
    data = response.json()["results"]["bindings"]

    print("about to group")
    return group(data, "nationality")  

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
            feature_blocks.append("?person wdt:P166 ?award.")

        elif category == "athlete":
            feature_blocks.append("?person wdt:P641 ?sport.")
            feature_blocks.append("?person wdt:P166 ?award.")
            feature_blocks.append("?person wdt:P54 ?team.")

        elif category == "singer":
            feature_blocks.append("?person wdt:P136 ?genre.")
            feature_blocks.append("?person wdt:P264 ?recordLabel.")
            feature_blocks.append("?person wdt:P1303 ?instrument.")
            feature_blocks.append("?person wdt:P166 ?award.")

        elif category == "politician":
            feature_blocks.append("?person wdt:P39 ?positionHeld.")

        elif category == "scientist":
            feature_blocks.append("?person wdt:P101 ?field.")
            feature_blocks.append("?person wdt:P69 ?educatedAt.")
            feature_blocks.append("?person wdt:P166 ?award.")

    feature_block = "\n      OPTIONAL { " + " }\n      OPTIONAL { ".join(feature_blocks) + " }"

    return f"""
    SELECT 
      ?person 
      ?nationality 
      ?birthCountry 
      (GROUP_CONCAT(DISTINCT ?occupationLabel; separator=",") AS ?occupations)
      (GROUP_CONCAT(DISTINCT ?awardLabel; separator=",") AS ?awards)
      (GROUP_CONCAT(DISTINCT ?sportLabel; separator=",") AS ?sports)
      (GROUP_CONCAT(DISTINCT ?genreLabel; separator=",") AS ?genres)
      (GROUP_CONCAT(DISTINCT ?teamLabel; separator=",") AS ?teams)
      (GROUP_CONCAT(DISTINCT ?instrumentLabel; separator=",") AS ?instruments)
      (GROUP_CONCAT(DISTINCT ?fieldLabel; separator=",") AS ?fields)
      (GROUP_CONCAT(DISTINCT ?educatedAtLabel; separator=",") AS ?schools)
       WHERE {{

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

