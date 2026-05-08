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

def country_to_continent(region): 
    if region in ["United States", "Canada", "Mexico"]:
        return "North America"

    elif region in ["United Kingdom", "France", "Germany", "Italy", "Spain", "Russia"]:
        return "Europe"

    elif region in ["China", "Japan", "India", "South Korea"]:
        return "Asia"

    elif region in ["Brazil", "Argentina", "Chile"]:
        return "South America"

    elif region in ["Nigeria", "South Africa", "Egypt"]:
        return "Africa"
    
    elif region in ["Australia"]:
        return "Australia"

    else:
        return "Other"
    
def nationality_buckets(person_data):
    region = person_data["nationality"]["value"]
    if region == None: 
        return None 
    else: 
        return country_to_continent(region)

def birth_place_buckets(person_data):
    region = person_data["birthCountry"]["value"]
    if region == None: 
        return None 
    else: 
        return country_to_continent(region)

def build_features(person_data):
    features = {}
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
        features["from_{country}"] = 1 if nationality_buckets(person_data) == country else 0
    
    for country in ["North America", "South America", "Europe", "Africa", "Asia", "Australia"]:
        features["born_in_{country}"] = 1 if birth_place_buckets(person_data) == country else 0
    
    
    

    

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

questions = ["is_male", "is_actor", "is_singer", "is_athlete", "age_under_30", "age_30_to_50","age_over_50"]

questions_remain = questions.copy()

person_found = False
while (len(questions_remain) > 0):
    to_ask = best_question(current_dataset, questions_remain)
    user_input = input(f"{to_ask.replace('_', ' ').capitalize()}? (y/n): ").strip().lower()
    answer = 1 if user_input == "y" else 0
    current_dataset = ask_question(current_dataset, to_ask, answer)
    
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