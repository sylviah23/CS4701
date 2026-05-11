GENDER_QUESTIONS = ["is_male"]


OCCUPATION_QUESTIONS = ["is_actor", 
                        "is_singer", 
                        "is_athlete", 
                        "is_politician", 
                        "is_scientist",
                        "is_director", 
                        "is_author", 
                        "is_comedian"]

AGE_QUESTIONS = ["age_under_30", 
                "age_30_to_50",
                "age_over_50"]

NATIONALITY_QUESTIONS = ["from_North_America", 
                         "from_South_America", 
                         "from_Europe", 
                         "from_Africa", 
                         "from_Asia", 
                         "from_Australia"]

ALL_QUESTIONS = GENDER_QUESTIONS + OCCUPATION_QUESTIONS + AGE_QUESIONS + NATIONALITY_QUESTIONS
QUESTION_CATEGORIES = [GENDER_QUESTIONS, OCCUPATION_QUESTIONS, AGE_QUESIONS, NATIONALITY_QUESTIONS]