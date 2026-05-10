import json
import get_data

CURRENT_YEAR = 2026

def get_age(birthday):
    if not birthday:
        return None
    birth_year = birthday[:birthday.index('-')]
    try:
      return CURRENT_YEAR - int(birth_year)
    except:
        return None

#maybe fade this and use the country_continent package pycountry-convert 
def country_to_continent(region): 
    if region in ["United States", "Canada", "Mexico"]:
        return "North_America"

    elif region in ["United Kingdom", "France", "Germany", "Italy", "Spain", "Russia", "Albania"]:
        return "Europe"

    elif region in ["China", "Japan", "India", "South Korea"]:
        return "Asia"

    elif region in ["Brazil", "Argentina", "Chile", "Colombia"]:
        return "South_America"

    elif region in ["Nigeria", "South Africa", "Egypt"]:
        return "Africa"
    
    elif region in ["Australia", "New Zealand"]:
        return "Australia"

    else:
        return "Other"
    
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
    for country in ["North_America", "South_America", "Europe", "Africa", "Asia", "Australia"]:
        if real_nat == country:
            features[f"from_{country}"] = 1
        else: 
            features[f"from_{country}"] = 0 #not sure if this needs to be stored tbh
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

with open("people.json","r") as f:
    people = json.load(f)

full_feature_dataset = {}
for person in people:
    name = person.get("personLabel").get("value")
    if name:
        full_feature_dataset[name] = build_features(person)

current_dataset = full_feature_dataset.copy() 

questions = ["is_male", "is_actor", "is_singer", "is_athlete", "is_politician", "is_scientist","age_under_30", "age_30_to_50","age_over_50"]
secondary_questions = ["from_North_America", "from_South_America", "from_Europe", "from_Africa", "from_Asia", "from_Australia"]

questions_remain = questions.copy()

person_found = False
nationalities_added = False 
while (len(questions_remain) > 0):
    to_ask = best_question(current_dataset, questions_remain)
    user_input = input(f"{to_ask.replace('_', ' ').capitalize()}? (y/n): ").strip().lower()
    answer = 1 if user_input == "y" else 0
    current_dataset = ask_question(current_dataset, to_ask, answer)
    if len(current_dataset) < 10: 
        for x in current_dataset: 
            print(x)
    questions_remain.remove(to_ask)
    
    if len(current_dataset) <= 100 and not nationalities_added:
        print(len(current_dataset))
        print("thinking...")
        new_data = get_data.get_nationality_trial(current_dataset)
        for person in current_dataset: 
            qid = current_dataset[person]["qid"]
            current_dataset[person] = build_nationality_trial(new_data[qid], current_dataset[person])
            

        questions_remain.extend(secondary_questions)
        nationalities_added = True

    if len(current_dataset) == 1:
        person_found = True
        print("I think your person is:", list(current_dataset.keys())[0])
        break

    elif len(current_dataset) == 0:
        print("Hmm, I couldn't find anyone matching those answers.")
        break
if (not person_found):
    print("Your person is one of the following names")

    for person,data in current_dataset.items():
        q = "is " + str(person)
        user_input = input(f"{q.replace('_', ' ').capitalize()}? (y/n): ").strip().lower()

        if user_input == 'y':
            print("I think your person is: " + str(person))