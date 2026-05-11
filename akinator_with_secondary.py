import json
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
    countries = [c.strip() for c in nationalities_string]
    continents = [country_to_continent(c) for c in countries]
    return max(set(continents), key=continents.count)


def birth_place_buckets(person_data):
    region = person_data["birthCountry"]["value"]
    if region == None: 
        return None 
    else: 
        return country_to_continent(region)


def build_gender_features(person_data, features):
    gender = person_data.get("genderLabel")
    if gender is None:
        return features
    if gender == "male":
        features["is_male"] = 1
        features["is_female"] = 0
    elif gender == "female":
        features["is_female"] = 1
        features["is_male"] = 0
    return features


def build_age_features(person_data, features):
    birthday = person_data.get("birthDate")
    if birthday is not None:
      age = get_age(birthday["value"])
      if age is not None:
          features["age_under_30"] = 1 if age < 30 else 0
          features["age_30_to_50"] = 1 if 30 <= age <= 50 else 0
          features["age_over_50"] = 1 if age > 50 else 0
    return features


def build_nationality_features(person_data, features):
    nationality = person_data.get("nationalities")
    if nationality != []:
        real_nat = nationality_buckets(nationality)
        for continent in ["North_America", "South_America", "Europe", "Africa", "Asia", "Australia"]:
            if real_nat == continent:
                features[f"from_{continent}"] = 1
            else: 
                features[f"from_{continent}"] = 0 #not sure if this needs to be stored tbh
    return features


def build_occupation_features(person_data, features):
    occupation = person_data.get("category")
    if occupation is not None:
        for category in ["actor", "athlete", "singer", "politician", "scientist", "musician", "director", "author", "comedian"]:
            features[f"is_{category}"] = 1 if category in person_data["category"]["value"] else 0
    return features


def build_award_features(person_data, features):
    awards = person_data.get("award_features")
    if awards is not None:
        for award in awards:
            features[award] = awards[award]
    return features


def build_secondary_feature(person_data, all_features, new_feature):
    feature = person_data.get(new_feature)
    if feature is not None:
        for f in feature:
            all_features[f] = feature[f]
    return all_features


def build_features(person_data):
    features = {}
    features = build_gender_features(person_data, features)
    features = build_age_features(person_data, features)
    features = build_nationality_features(person_data, features)
    features = build_occupation_features(person_data, features)
    features = build_secondary_feature(person_data, features,"award_features")
    features = build_secondary_feature(person_data, features,"sport_features")
    features = build_secondary_feature(person_data, features,"position_features")
    features = build_secondary_feature(person_data, features,"field_features")
    features = build_secondary_feature(person_data, features,"instrument_features")

    return features


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


# this removes any questions that does not help the akinator. that is, if all the people
# remaining would say "yes" to a question or all say "no", asking this question adds no
# value and can be removed
def remove_null_questions(questions, dataset):
    questions_to_remove = []
    for q in range(len(questions)): 
        count = 0 

        for _, data in dataset.items():
            if data.get(questions[q], 0) == 1: 
                count += 1 

        if count == 0 or count == len(dataset):
            questions_to_remove.append(questions[q])
                
    for q in questions_to_remove:
        questions.remove(q)
    return questions


# goes down the list of the remaining people in the dataset and asks user if
# answer is each person on the list.
# returns: True if person was found correctly, False if not
def ask_individuals(current_dataset):
    for qid, data in current_dataset.items():
        name = data.get("name", qid)
        q = f"is {name}"
        user_input = input(f"{q.replace('_', ' ').capitalize()}? (y/n): ").strip().lower()
        if user_input == 'y':
            print("I think your person is: " + name)
            return True

    return False


def build_all_features(people):
    full_feature_dataset = {}
    for person in people:
        name = person.get("personLabel").get("value")
        qid = person["person"]["value"].split("/")[-1]
        full_feature_dataset[qid] = build_features(person)
        full_feature_dataset[qid]["name"] = name
    return full_feature_dataset


def add_secondary_data_user_answer(question, json_category, json_entry):
    if json_category not in json_entry:
        json_entry[json_category] = {}
    if answer == "y":
        json_entry[json_category][question] = 0
    else:
        json_entry[json_category][question] = 1
    return json_entry
    

def write_user_answer(json_entry):
    with open("people_enriched.json","r") as file:
        data = json.load(file)
    
    data.append(json_entry)

    with open('people_enriched.json', 'w') as file:
        json.dump(data, file,indent=2)


def add_user_answer(user_answer,question_answer_cache, birthday, nationality):
    json_entry = {  "person": {
                    "value": "Q0" 
                    },
                    "personLabel": {
                    "value": user_answer
                    },
                    "nationalities": [
                        nationality
                    ],
                    "birthDate": {
                    "value": birthday
                    }
                }
    for question, answer in question_answer_cache.items():
        if question in questions_bank.GENDER_QUESTIONS:
            if answer == "y":
                json_entry["genderLabel"] = {"value": "male"}
            else:
                json_entry["genderLabel"] = {"value": "female"}
        if question in questions_bank.OCCUPATION_QUESTIONS:
            if answer == "y":
                json_entry["category"] = {"value": question.split('_')[1]}
        if question in questions_bank.SPORTS_QUESTIONS:
            json_entry = add_secondary_data_user_answer(question, "sport_features", json_entry)
        if question in questions_bank.AWARD_QUESTIONS:
            json_entry = add_secondary_data_user_answer(question, "award_features", json_entry)
        if question in questions_bank.INSTRUMENT_QUESTIONS:
            json_entry = add_secondary_data_user_answer(question, "instrument_features", json_entry)
        if question in questions_bank.POLITICIAN_QUESTIONS:
            json_entry = add_secondary_data_user_answer(question, "position_features", json_entry)
        if question in questions_bank.SCIENTIST_QUESTIONS:
            json_entry = add_secondary_data_user_answer(question, "field_features", json_entry)

    write_user_answer(json_entry)


if __name__ == "__main__":
    with open("people_enriched.json","r") as f:
        people = json.load(f)
    current_dataset = build_all_features(people)
    questions_remain = questions_bank.ALL_QUESTIONS
    question_answer_cache = {} # store user's Q&A in case their person is not in dataset we can add them in at game over

    person_found = False
    while (len(questions_remain) > 0):
        to_ask = best_question(current_dataset, questions_remain)
        user_input = input(f"{to_ask.replace('_', ' ').capitalize()}? (y/n): ").strip().lower()
        question_answer_cache[to_ask] = user_input
        answer = 1 if user_input == "y" else 0
        current_dataset = ask_question(current_dataset, to_ask, answer)
        questions_remain = remove_null_questions(questions_remain, current_dataset)
        
        # dataset only has 1 or 0 people, break and ask for it directly below or say you can't find it
        if len(current_dataset) <= 1:
            break

    if (not person_found):
        person_found = ask_individuals(current_dataset)

    if (not person_found):
        print("Hmm, I couldn't find anyone matching those answers.")
        user_answer = input(f"Please input your person's name: ")
        birthday = input(f"Please input their birthday in the format YYYY-MM-DD: ")
        nationality = input(f"Please input their nationality (name of the country): ")
        add_user_answer(user_answer,question_answer_cache, birthday, nationality)
        