GENDER_QUESTIONS = ["is_male"]

ALIVE_QUESTIONS = ["is_alive"]

OCCUPATION_QUESTIONS = ["is_actor", 
                        "is_singer", 
                        "is_athlete", 
                        "is_politician", 
                        "is_scientist",
                        "is_director", 
                        "is_author", 
                        "is_comedian",
                        "is_musician",
                        "is_businessman",
                        "is_entrepreneur",
                        "is_architect",
                        "is_philosopher",
                        "is_explorer",
                        "is_inventor",
                        "is_journalist",
                        "is_chef",
                        "is_fashion_designer",
                        "is_activist",
                        "is_monarch",
                        "is_military_leader",
                        "is_painter",
                        "is_mathematician",
                        "is_revolutionary",
                        "is_theologian",
                        "is_sculptor"]

AGE_QUESTIONS = ["age_under_30", 
                 "age_30_to_50",
                 "age_over_50"]

NATIONALITY_QUESTIONS = ["from_North_America", 
                         "from_South_America", 
                         "from_Europe", 
                         "from_Africa", 
                         "from_Asia", 
                         "from_Australia"]

SPORTS_QUESTIONS = ["plays_team_sport",
                    "plays_racket_sport",
                    "plays_combat_sport",
                    "plays_racing_sport",
                    "plays_water_sport",
                    "plays_winter_sport",
                    "plays_track_field",
                    "plays_golf",
                    "plays_gymnastics"]

AWARD_QUESTIONS = ["won_oscar",
                   "won_emmy",
                   "won_tony",
                   "won_grammy",
                   "won_nobel",
                   "won_olympic"]

INSTRUMENT_QUESTIONS = ["plays_strings",
                        "plays_keys",
                        "plays_wind",
                        "plays_percussion",
                        "plays_vocals"]

POLITICIAN_QUESTIONS = ["is_president",
                        "is_prime_minister",
                        "is_senator_or_mp",
                        "is_governor",
                        "is_minister"]

SCIENTIST_QUESTIONS = ["field_physical_science",
                       "field_life_science",
                       "field_social_science",
                       "field_computer_science"]

ALL_QUESTIONS = (ALIVE_QUESTIONS + GENDER_QUESTIONS + OCCUPATION_QUESTIONS +
                 AGE_QUESTIONS + NATIONALITY_QUESTIONS + SPORTS_QUESTIONS +
                 AWARD_QUESTIONS + INSTRUMENT_QUESTIONS + POLITICIAN_QUESTIONS +
                 SCIENTIST_QUESTIONS)

QUESTION_CATEGORIES = [ALIVE_QUESTIONS, GENDER_QUESTIONS, OCCUPATION_QUESTIONS,
                       AGE_QUESTIONS, NATIONALITY_QUESTIONS, SPORTS_QUESTIONS,
                       AWARD_QUESTIONS, INSTRUMENT_QUESTIONS, POLITICIAN_QUESTIONS,
                       SCIENTIST_QUESTIONS]