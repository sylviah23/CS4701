import json
import questions_bank
from pycountry_convert import country_alpha2_to_continent_code
import pycountry
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.text import Text
from rich import box
from rich.rule import Rule
import math 

console = Console()
CURRENT_YEAR = 2026

# helpers

def get_age(birthday):
    if not birthday:
        return None
    try:
        return CURRENT_YEAR - int(birthday[:birthday.index('-')])
    except:
        return None

def country_to_continent(region):
    try:
        country = pycountry.countries.lookup(region)
        code = country_alpha2_to_continent_code(country.alpha_2)
    except:
        return None
    return {"NA":"North_America","EU":"Europe","AS":"Asia",
            "SA":"South_America","AF":"Africa","OC":"Australia"}.get(code)

def nationality_buckets(nationalities):
    if not nationalities:
        return None
    continents = [country_to_continent(c.strip()) for c in nationalities]
    continents = [c for c in continents if c]
    return max(set(continents), key=continents.count) if continents else None

def build_secondary_feature(person_data, all_features, key):
    feature = person_data.get(key)
    if feature:
        for f in feature:
            all_features[f] = feature[f]
    return all_features

def build_features(person_data):
    features = {}

    gender = person_data.get("genderLabel", {}).get("value") if isinstance(person_data.get("genderLabel"), dict) else person_data.get("genderLabel")
    if gender == "male":
        features["is_male"] = 1
    elif gender == "female":
        features["is_male"] = 0

    birthday = person_data.get("birthDate")
    if birthday:
        val = birthday.get("value") if isinstance(birthday, dict) else birthday
        age = get_age(val)
        if age is not None:
            features["age_under_30"] = 1 if age < 30 else 0
            features["age_30_to_50"] = 1 if 30 <= age <= 50 else 0
            features["age_over_50"] = 1 if age > 50 else 0

    nationality = person_data.get("nationalities", [])
    if nationality:
        real_nat = nationality_buckets(nationality)
        for continent in ["North_America","South_America","Europe","Africa","Asia","Australia"]:
            features[f"from_{continent}"] = 1 if real_nat == continent else 0

    category = person_data.get("category", {}).get("value", "")
    for cat in ["actor", "athlete", "singer", "politician", "scientist", "musician",
                "director", "author", "comedian", "businessman", "entrepreneur",
                "architect", "philosopher", "explorer", "inventor", "journalist",
                "chef", "fashion_designer", "activist", "monarch", "military_leader",
                "painter", "mathematician", "revolutionary", "theologian", "sculptor"]:
        features[f"is_{cat}"] = 1 if cat in category else 0

    is_alive = person_data.get("is_alive")
    if is_alive is not None:
        features["is_alive"] = is_alive

    for key in ["award_features","sport_features","position_features","field_features","instrument_features"]:
        features = build_secondary_feature(person_data, features, key)

    return features

def get_total_site_links(people):
    count = 0
    for person in people:
        count += int(person.get("sitelinks", {}).get("value", "0"))
    return count

def build_all_features(people):
    total_site_links = get_total_site_links(people)

    dataset = {}
    for person in people:
        name = person.get("personLabel", {}).get("value", "Unknown")
        qid = person["person"]["value"].split("/")[-1]
        dataset[qid] = build_features(person)
        dataset[qid]["name"] = name

        # initial prior probabilities are equal to the site links / total site links
        # if there are no site links associated with a person it defaults to 1
        site_links = int(person.get("sitelinks", {}).get("value", "1"))
        dataset[qid]["prob"] = site_links / total_site_links

    return dataset

def best_question(dataset, questions): 
    best_q, best_score = questions[0], -1
    n = len(dataset)
    for q in questions:
        count = sum(1 for d in dataset.values() if d.get(q, 0) == 1)
        score = (count / n) * (1 - count / n)
        if score > best_score:
            best_score, best_q = score, q
    return best_q

# def best_question(dataset, questions): #selecting a best question with entropy 
# weighting yes and no by the current probabilities in the database
#     best_q = None
#     best_score = -float("inf")  # entropy: lower is better

#     total_mass = sum(d["prob"] for d in dataset.values())
#     if total_mass == 0:
#         return questions[0]

#     for q in questions:
#         p_yes = 0.0
#         p_no = 0.0

#         for d in dataset.values():
#             prob = d["prob"]

#             if d.get(q, 0) == 1:
#                 p_yes += prob
#             else:
#                 p_no += prob

#         # normalize
#         p_yes /= total_mass
#         p_no /= total_mass

#         # avoid log(0)
#         if p_yes == 0 or p_no == 0:
#             score = 0
#         else:
#             score = -(
#                 p_yes * math.log(p_yes) +
#                 p_no * math.log(p_no)
#             )

#         if score > best_score:
#             best_score = score
#             best_q = q

#     return best_q

#normalizes the recomputed probabilities for ask_question 
#removes entries with very low probabilities 
def normalize_probabilities(dataset, total, threshold): 
    filtered = {}
    #most_likely = 0
    for name, data in dataset.items(): 
        new_prob =  dataset[name]["prob"]/total
        dataset[name]["prob"] = new_prob
        if new_prob >= threshold or threshold == -1: 
            filtered[name] = data 
        #most_likely = max(most_likely, new_prob)
    # for name, data in dataset.items(): 
    #     new_prob = dataset[name]["prob"]
        # if new_prob >= threshold or threshold == -1: 
        #     filtered[name] = data 
    return filtered 

def update_probs(dataset, question, answer, user_input, threshold):
    updated = {}
    total = 0
    
    for name, data in dataset.items():
        feature_val = data.get(question, 0)

        p = 1

        if feature_val == answer: #agreeing with user answer 
            if answer == 0: #
                if user_input == "n":
                    p = 0.9
                if user_input == "mb":
                    p = 0.75
            elif answer == 1: 
                if user_input == "y":
                    p = 0.9
                if user_input == "my":
                    p = 0.75
        else: 
            if answer == 0: #
                if user_input == "n":
                    p = 0.1
                if user_input == "mb":
                    p = 0.25
            elif answer == 1: 
                if user_input == "y":
                    p = 0.1
                if user_input == "my":
                    p = 0.25
        
        new_p = data["prob"] * p
        
        updated[name] = data.copy()
        updated[name]["prob"] = new_p
    
        total += new_p

    # normalize 
    updated = normalize_probabilities(updated, total, threshold)
    
    return updated

def very_likely_person(dataset, threshold):
    candidates = {
        k: v for k, v in dataset.items()
        if v["prob"] >= threshold
    }

    return (len(candidates) > 0, candidates)

def splice_wrong_people(curr_data, new_data):
    to_ret = {
        k: v for k, v in curr_data.items()
        if k not in new_data
    }

    total = sum(v["prob"] for v in to_ret.values())

    if total == 0:
        return to_ret

    for v in to_ret.values():
        v["prob"] /= total

    return to_ret

def filter_dataset(dataset, question, answer):
    return {k: v for k, v in dataset.items() if v.get(question, 0) == answer}

def remove_null_questions(questions, dataset):
    n = len(dataset)
    return [q for q in questions if 0 < sum(1 for d in dataset.values() if d.get(q, 0) == 1) < n]

# question labels 

QUESTION_LABELS = {
    "is_male":             "Is your person male?",
    "is_alive":            "Is your person still alive?",
    "age_under_30":        "Is your person under 30 years old?",
    "age_30_to_50":        "Is your person between 30 and 50 years old?",
    "age_over_50":         "Is your person over 50 years old?",
    "from_North_America":  "Is your person from North America?",
    "from_South_America":  "Is your person from South America?",
    "from_Europe":         "Is your person from Europe?",
    "from_Africa":         "Is your person from Africa?",
    "from_Asia":           "Is your person from Asia?",
    "from_Australia":      "Is your person from Australia?",
    "is_actor":            "Is your person an actor?",
    "is_singer":           "Is your person a singer?",
    "is_athlete":          "Is your person an athlete?",
    "is_politician":       "Is your person a politician?",
    "is_scientist":        "Is your person a scientist?",
    "is_musician":         "Is your person a musician?",
    "is_director":         "Is your person a film director?",
    "is_author":           "Is your person an author or writer?",
    "is_comedian":         "Is your person a comedian?",
    "is_businessman":      "Is your person a businessman?",
    "is_entrepreneur":     "Is your person an entrepreneur?",
    "is_architect":        "Is your person an architect?",
    "is_philosopher":      "Is your person a philosopher?",
    "is_explorer":         "Is your person an explorer?",
    "is_inventor":         "Is your person an inventor?",
    "is_journalist":       "Is your person a journalist?",
    "is_chef":             "Is your person a chef?",
    "is_fashion_designer": "Is your person a fashion designer?",
    "is_activist":         "Is your person an activist?",
    "is_monarch":          "Is your person a monarch (king/queen)?",
    "is_military_leader":  "Is your person a military leader?",
    "is_painter":          "Is your person a painter?",
    "is_mathematician":    "Is your person a mathematician?",
    "is_revolutionary":    "Is your person a revolutionary?",
    "is_theologian":       "Is your person a theologian?",
    "is_sculptor":         "Is your person a sculptor?",
    "won_oscar":           "Has your person won an Oscar?",
    "won_emmy":            "Has your person won an Emmy?",
    "won_tony":            "Has your person won a Tony Award?",
    "won_grammy":          "Has your person won a Grammy?",
    "won_nobel":           "Has your person won a Nobel Prize?",
    "won_olympic":         "Has your person won an Olympic medal?",
    "plays_team_sport":    "Does your person play a team sport (football, basketball, etc.)?",
    "plays_racket_sport":  "Does your person play a racket sport (tennis, badminton, etc.)?",
    "plays_combat_sport":  "Does your person do a combat sport (boxing, wrestling, etc.)?",
    "plays_racing_sport":  "Does your person do racing (F1, cycling, etc.)?",
    "plays_water_sport":   "Does your person do a water sport (swimming, diving, etc.)?",
    "plays_winter_sport":  "Does your person do a winter sport (skiing, skating, etc.)?",
    "plays_track_field":   "Does your person do track & field (running, marathon, etc.)?",
    "plays_golf":          "Does your person play golf?",
    "plays_gymnastics":    "Does your person do gymnastics?",
    "plays_strings":       "Does your person play a string instrument (guitar, violin, etc.)?",
    "plays_keys":          "Does your person play keys (piano, keyboard, etc.)?",
    "plays_wind":          "Does your person play a wind instrument (trumpet, flute, etc.)?",
    "plays_percussion":    "Does your person play percussion/drums?",
    "plays_vocals":        "Is your person primarily a vocalist/singer?",
    "is_president":        "Has your person been a president?",
    "is_prime_minister":   "Has your person been a prime minister?",
    "is_senator_or_mp":    "Has your person been a senator or MP?",
    "is_governor":         "Has your person been a governor?",
    "is_minister":         "Has your person been a government minister?",
    "field_physical_science": "Does your person work in physical sciences (physics, chemistry, etc.)?",
    "field_life_science":     "Does your person work in life sciences (biology, medicine, etc.)?",
    "field_social_science":   "Does your person work in social sciences (psychology, economics, etc.)?",
    "field_computer_science": "Does your person work in computer science or engineering?",
}

def ask(question, remaining):
    label = QUESTION_LABELS.get(question, question.replace("_", " ").capitalize() + "?")
    console.print(f"\n[bold cyan]Q:[/bold cyan] {label}")
    console.print(f"[dim]({remaining} people remaining)[/dim]")
    console.print(
        "[dim]"
        "y = yes    "
        "my = maybe yes    "
        "mb = maybe no    "
        "n = no"
        "[/dim]"
    )

    while True:
        answer = Prompt.ask("[bold]Your answer[/bold]", choices=["y", "my", "mb", "n"], default="y")
        if answer in ("y", "my", "mb", "n"):
            return answer

def add_user_answer(user_answer, question_answer_cache, birthday, nationality):
    json_entry = {
        "person": {"value": "Q0"},
        "personLabel": {"value": user_answer},
        "nationalities": [nationality],
        "birthDate": {"value": birthday},
        "genderLabel": {"value": ""},
        "category": {"value": ""},
        "is_alive": None,
    }
    for question, answer in question_answer_cache.items():
        if question == "is_alive":
            json_entry["is_alive"] = 1 if answer == "y" else 0
        if question == "is_male":
            json_entry["genderLabel"]["value"] = "male" if answer == "y" else "female"
        if question in questions_bank.OCCUPATION_QUESTIONS and answer == "y":
            json_entry["category"]["value"] = question.replace("is_", "")
        for feat_key, q_list in [
            ("sport_features",      questions_bank.SPORTS_QUESTIONS),
            ("award_features",      questions_bank.AWARD_QUESTIONS),
            ("instrument_features", questions_bank.INSTRUMENT_QUESTIONS),
            ("position_features",   questions_bank.POLITICIAN_QUESTIONS),
            ("field_features",      questions_bank.SCIENTIST_QUESTIONS),
        ]:
            if question in q_list:
                if feat_key not in json_entry:
                    json_entry[feat_key] = {}
                json_entry[feat_key][question] = 1 if answer == "y" else 0

    with open("people_enriched.json", "r") as f:
        data = json.load(f)
    data.append(json_entry)
    with open("people_enriched.json", "w") as f:
        json.dump(data, f, indent=2)
    console.print(f"\n[green]✓ Added [bold]{user_answer}[/bold] to the database![/green]")

# main game loop

def main():
    console.print(Panel.fit(
        "[bold magenta]🧞 AKINATOR[/bold magenta]\n[dim]Think of a famous person and I'll try to guess who it is.[/dim]",
        box=box.DOUBLE,
        border_style="magenta"
    ))
    console.print("\n[dim]Press Enter to start...[/dim]")
    input()

    with open("people_enriched.json", "r") as f:
        people = json.load(f)

    current_dataset = build_all_features(people)
    questions_remain = questions_bank.ALL_QUESTIONS.copy()
    question_answer_cache = {}

    console.print(f"\n[dim]Database loaded: {len(current_dataset)} people[/dim]")
    console.print(Rule(style="dim"))

    person_found = False

    num_questions_asked = 0

    while len(questions_remain) > 0 and len(current_dataset) > 1:
        to_ask = best_question(current_dataset, questions_remain)
        user_input = ask(to_ask, len(current_dataset))
        question_answer_cache[to_ask] = user_input
        answer = 1 if (user_input == "y" or user_input == "my") else 0
        if num_questions_asked < 3:
            current_dataset = update_probs(current_dataset, to_ask, answer, user_input, -1)
        else:
            current_dataset = update_probs(current_dataset, to_ask, answer, user_input, 0.0001)
        # current_dataset = filter_dataset(current_dataset, to_ask, answer)
        questions_remain.remove(to_ask)
        questions_remain = remove_null_questions(questions_remain, current_dataset) #no longer removing null questions 
        #since the dataset doesn't change -- this can be modified 

        likely, new_data = very_likely_person(current_dataset, 0.15) #current threshold at 0.5
        if likely: 
            for qid, data in current_dataset.items(): 
                name = data.get("name", qid)
                console.print(Panel.fit(
            f"[bold]Is your person [magenta]{name}[/magenta]?[/bold]",
            border_style="yellow"
        ))
                answer = Prompt.ask("[bold]Your answer[/bold]", choices=["y", "n"])
                if answer == "y":
                    console.print(Panel.fit(
                    f"[bold green]🎉 I got it! Your person is {name}![/bold green]",
                    border_style="green"
            ))
                    person_found = True
                    break
                if not person_found: 
                    current_dataset = splice_wrong_people(current_dataset, new_data)
        num_questions_asked += 1

    console.print(Rule(style="dim"))
    console.print("\n[bold yellow]🤔 Let me think...[/bold yellow]\n")

    sorted_current_dataset = sorted(
        current_dataset.items(),
        key=lambda item: item[1]["prob"],
        reverse=True
    )

    for qid, data in sorted_current_dataset:
        name = data.get("name", qid)
        console.print(Panel.fit(
            f"[bold]Is your person [magenta]{name}[/magenta]?[/bold]",
            border_style="yellow"
        ))
        answer = Prompt.ask("[bold]Your answer[/bold]", choices=["y", "n"])
        if answer == "y":
            console.print(Panel.fit(
                f"[bold green]🎉 I got it! Your person is {name}![/bold green]",
                border_style="green"
            ))
            person_found = True
            break

    if not person_found:
        console.print(Panel.fit(
            "[bold red]😔 I couldn't figure it out! You stumped me.[/bold red]",
            border_style="red"
        ))
        user_answer = Prompt.ask("\n[bold]Who was your person?[/bold]")
        birthday = Prompt.ask("[bold]Their birthday[/bold] [dim](YYYY-MM-DD)[/dim]")
        nationality = Prompt.ask("[bold]Their nationality[/bold] [dim](country name)[/dim]")
        add_user_answer(user_answer, question_answer_cache, birthday, nationality)

    console.print("\n[dim]Thanks for playing![/dim]\n")

if __name__ == "__main__":
    main()