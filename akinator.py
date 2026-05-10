import json
import get_data
import questions_bank
from pycountry_convert import country_alpha2_to_continent_code
import pycountry

CURRENT_YEAR = 2026

def get_age(birthday):
    if not birthday:
        return None
    birth_year = birthday[:birthday.index('-')]
    try:
      return CURRENT_YEAR - int(birth_year)
    except:
        return None

def country_to_continent(region):
    try:
        country = pycountry.countries.lookup(region)
        code = country_alpha2_to_continent_code(country.alpha_2)
    except:
        return None

    mapping = {
        "NA": "North_America",
        "EU": "Europe",
        "AS": "Asia",
        "SA": "South_America",
        "AF": "Africa",
        "OC": "Australia"
    }

    return mapping[code]
    
def nationality_buckets(nationalities_string):
    if nationalities_string == None: 
        return None 
    countries = [c.strip() for c in nationalities_string.split(",")]
    continents = [country_to_continent(c) for c in countries]
    return max(set(continents), key=continents.count)

def birth_place_buckets(person_data):
    region = person_data["birthCountry"]["value"]
    if region == None: 
        return None 
    else: 
        return country_to_continent(region)

def awards_buckets(person_data):
    if person_data["awards"]["value"] == None: 
        return None 
    awards = set(person_data["awards"]["value"].split(","))
    to_ret = set()
    for x in awards: 
        
        if "Emmy" in x: 
            to_ret.add("Emmy")
        if "Tony" in x: 
            to_ret.add("Tony")
        if "Oscar" in x: 
            to_ret.add("Oscar")
        if "Grammy" in x: 
            to_ret.add("Grammy")
        #Non-entertainment awards are likely to only win one of all awards 
        elif "Nobel" in x: 
            to_ret.add("Nobel")
            break
        elif "Olympic" in x: 
            to_ret.add("Olympic")
            break 
        
        elif "Pulitzer" in x: 
            to_ret.add("Pulitzer")
            break 

    return list(to_ret) 

def sports_buckets(person_data):
    if person_data["sports"]["value"] == None: 
        return None 
    sports = set(person_data["sports"]["value"].split(","))
    to_ret = set()
    #chat has given me this data set, to do: query atheletes and see sports outputs, 
    #edit the dataset accordingly 
    SPORT_BUCKETS = {
    "team_sports": {
        "association football",
        "basketball",
        "baseball",
        "american football",
        "cricket",
        "hockey",
        "rugby"
    },

    "combat_sports": {
        "boxing",
        "mixed martial arts",
        "wrestling",
        "judo",
        "karate"
    },

    "racing_sports": {
        "formula one",
        "nascar",
        "motorcycle racing",
        "rallying"
    },

    "water_sports": {
        "swimming",
        "diving",
        "surfing",
        "water polo"
    },

    "winter_sports": {
        "skiing",
        "snowboarding",
        "figure skating",
        "ice hockey"
    },

    "track_and_field": {
        "running",
        "marathon",
        "pole vault"
    },

    "racket_sports": {
        "tennis",
        "badminton",
        "table tennis",
        "squash"
    },

    "strength_precision": {
        "golf",
        "archery",
        "shooting sport",
        "weightlifting"
    },

    "extreme_sports": {
        "skateboarding",
        "bmx",
        "rock climbing"
    }
}
  
    for sport in sports: 

        sport = sport.lower()
        for bucket, words in SPORT_BUCKETS.items():
            for word in words: 
                if word in sport: 
                    to_ret.add(bucket)
                    break 

    return list(to_ret)


#no bucket building can be abstracted
# def build_no_buckets(trait, person_data, features):
#     traits = None
#     if person_data[f"{trait}"]["value"] != None: 
#         traits = set(person_data[f"{trait}"]["value"].split(","))
#     for x in traits 

def build_nationality_trial(person_data, features):
    # nationality = person_data.get("nationalities")
    nationality = person_data
    if not nationality:
        return features
    
    real_nat = nationality_buckets(nationality)
    for continent in ["North_America", "South_America", "Europe", "Africa", "Asia", "Australia"]:
        if real_nat == continent:
            features[f"from_{continent}"] = 1
        else: 
            features[f"from_{continent}"] = 0 #not sure if this needs to be stored tbh
    return features 

def build_features(person_data):
    features = {}
    qid = person_data["person"]["value"].split("/")[-1]
    features["qid"] = qid

    if person_data["genderLabel"]["value"] == "male":
        features["is_male"] = 1
        features["is_female"] = 0
    elif person_data["genderLabel"]["value"] == "female":
        features["is_female"] = 1
        features["is_male"] = 0
    
    for category in ["actor", "athlete", "singer", "politician", "scientist"]:
        features[f"is_{category}"] = 1 if category in person_data["category"]["value"] else 0
    
    birthday = person_data.get("birthDate")
    if birthday is not None:
      age = get_age(birthday["value"])
      if age is not None:
          features["age_under_30"] = 1 if age < 30 else 0
          features["age_30_to_50"] = 1 if 30 <= age <= 50 else 0
          features["age_over_50"] = 1 if age > 50 else 0
    return features


def build_secondary_features(person_data):
    features = {}
    for country in ["North America", "South America", "Europe", "Africa", "Asia", "Australia"]:
        if nationality_buckets(person_data) == country:
            features[f"from_{country}"] = 1 
    
    for country in ["North America", "South America", "Europe", "Africa", "Asia", "Australia"]:
         if birth_place_buckets(person_data) == country:
            features[f"born_in_{country}"] = 1
    #occupation build here 
    # occupations = set(person_data.get("occupations", {}).get("value", "").split(",")) - {""}
    #awards build -- if you think of others please add 
    if person_data["category"]["value"] != "politician":
        for award in ["Grammy", "Tony", "Emmy", "Nobel", "Oscar", "Olympic", "Pulitzer"]:
            awards = awards_buckets(person_data)
            if award in awards: 
                features[f"{award}_won"] = 1

    if person_data["category"]["value"] == "athlete":
        if person_data["sports"]["value"] != None: 
            sports = set(person_data["sports"]["value"].split(","))
            for x in sports: 
                #Is this too specific and shld only be stored when the sport bucket questions are asked?
                features[f"play_{x}"] = 1
            for bucket in sports_buckets(person_data): 
                features[f"sport_type_{bucket}"] = 1

    #need to check singer category 
    if person_data["instruments"]["value"] != None: 
        instruments = set(person_data["instruments"]["value"].split(","))
        for x in instruments: 
            features[f"play_{x}"] = 1
    

def best_question(dataset, questions):
    max = -1
    index = -1
    len_data = len(dataset.items())

    for q in range(len(questions)): 
        count = 0 

        for _, data in dataset.items():
            if data.get(questions[q], 0) == 1: 
                count += 1 

            fraction = count/len_data

            if ((fraction)*(1-fraction)) > max: 
                max = (fraction)*(1-fraction)
                index = q
                
    return questions[index]
            
def ask_question(dataset, question, answer):
    filtered = {}
    for name, data in dataset.items():
        if data.get(question, 0) == answer:
            filtered[name] = data
    return filtered

def remove_question_category(questions_remain,to_ask):
    for category in questions_bank.QUESTION_CATEGORIES:
        if to_ask in category:
            for q in category:
                if q in questions_remain:
                    questions_remain.remove(q)
    return questions_remain

# goes down the list of the remaining people in the dataset and asks user if
# answer is each person on the list.
# returns: True if person was found correctly, False if not
def ask_individuals(current_dataset):
    person_found = False
    for person,_ in current_dataset.items():
        q = "is " + str(person)
        user_input = input(f"{q.replace('_', ' ').capitalize()}? (y/n): ").strip().lower()

        if user_input == 'y':
            print("I think your person is: " + str(person))
            person_found = True
            break
    return person_found

with open("people.json","r") as f:
    people = json.load(f)

# builds all initial features (gender, occupation, age)
def build_initial_features():
    full_feature_dataset = {}
    for person in people:
        name = person.get("personLabel").get("value")
        if name:
            full_feature_dataset[name] = build_features(person)
    return full_feature_dataset

if __name__ == "__main__":
    current_dataset = build_initial_features()
    questions_all = questions_bank.ALL_QUESTIONS_INITIAL
    questions_remain = questions_all.copy()

    person_found = False
    nationalities_added = False 
    while (len(questions_remain) > 0):
        to_ask = best_question(current_dataset, questions_remain)
        user_input = input(f"{to_ask.replace('_', ' ').capitalize()}? (y/n): ").strip().lower()
        answer = 1 if user_input == "y" else 0
        current_dataset = ask_question(current_dataset, to_ask, answer)
        if user_input == "y":
            questions_remain = remove_question_category(questions_remain,to_ask)
        else:
            questions_remain.remove(to_ask)

        # add nationality questions if <= 100 left in dataset
        if len(current_dataset) <= 100 and not nationalities_added:
            print("thinking...")
            new_data = get_data.get_nationality_trial(current_dataset)
            for person in current_dataset: 
                qid = current_dataset[person]["qid"]
                current_dataset[person] = build_nationality_trial(new_data[qid], current_dataset[person])
                
            questions_remain.extend(questions_bank.NATIONALITY_QUESTIONS)
            nationalities_added = True

        # dataset only has 1 or 0 people, break and ask for it directly below or
        # say you can't find it
        if len(current_dataset) <= 1:
            break

    if (not person_found):
        person_found = ask_individuals(current_dataset)

    if (not person_found):
        print("Hmm, I couldn't find anyone matching those answers.")