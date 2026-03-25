import json

CURRENT_YEAR = 2026

def get_age(birthday):
    if not birthday:
        return None
    birth_year = birthday[:birthday.index('-')]
    try:
      return CURRENT_YEAR - int(birth_year)
    except:
        return None

def build_features(person_data):
    features = {}
    if person_data["genderLabel"]["value"] == "male":
        features["is_male"] = 1
    elif person_data["genderLabel"]["value"] == "female":
        features["is_female"] = 1
    
    for category in ["actor", "athlete", "singer"]:
        features[f"is_{category}"] = 1 if category in person_data["category"]["value"] else 0
    
    birthday = person_data.get("birthDate")
    if birthday is not None:
      age = get_age(birthday["value"])
      if age is not None:
          features["age_under_30"] = 1 if age < 30 else 0
          features["age_30_to_50"] = 1 if 30 <= age <= 50 else 0
          features["age_over_50"] = 1 if age > 50 else 0
    return features

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

for q in questions:
    user_input = input(f"{q.replace('_', ' ').capitalize()}? (y/n): ").strip().lower()
    answer = 1 if user_input == "y" else 0
    current_dataset = ask_question(current_dataset, q, answer)

    if len(current_dataset) == 1:
        print("I think your person is:", list(current_dataset.keys())[0])
        break
    elif len(current_dataset) == 0:
        print("Hmm, I couldn't find anyone matching those answers.")
        break

for person,data in current_dataset.items():
    q = "is " + str(person)
    user_input = input(f"{q.replace('_', ' ').capitalize()}? (y/n): ").strip().lower()

    if user_input == 'y':
      print("I think your person is: " + str(person))