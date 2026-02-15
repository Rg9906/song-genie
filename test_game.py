from backend.logic.engine import Engine
from backend.logic.belief import update_beliefs
from backend.logic.questions import select_best_question

CONFIDENCE_THRESHOLD = 0.85
DOMINANCE_RATIO = 3.0
MAX_QUESTIONS = 20


engine = Engine()

songs = engine.get_entities()

beliefs = engine.get_beliefs()

questions = engine.get_questions()

asked = set()

for step in range(MAX_QUESTIONS):

    # Sort beliefs
    sorted_beliefs = sorted(
        beliefs.items(),
        key=lambda x: x[1],
        reverse=True
    )

    best_id, p1 = sorted_beliefs[0]
    p2 = sorted_beliefs[1][1] if len(sorted_beliefs) > 1 else 0.0

    print("\nCurrent top probability:", p1)

    # Condition 1: Absolute confidence
    if p1 >= CONFIDENCE_THRESHOLD:
        print("\nHigh absolute confidence reached.")
        break

    # Condition 2: Relative dominance
    if p2 > 0 and (p1 / p2) >= DOMINANCE_RATIO:
        print("\nStrong dominance over second candidate.")
        break

    # Ask next question
    question = select_best_question(
        questions,
        songs,
        beliefs,
        asked
    )

    if question is None:
        print("\nNo more useful questions.")
        break

    print("\nQuestion:", question["text"])

    answer = input("Answer (yes/no/unsure): ")

    beliefs = update_beliefs(
        beliefs,
        songs,
        question["feature"],
        question["value"],
        answer
    )

    asked.add((question["feature"], question["value"]))


# Final evaluation
sorted_beliefs = sorted(
    beliefs.items(),
    key=lambda x: x[1],
    reverse=True
)

best_id, best_prob = sorted_beliefs[0]

if best_prob >= CONFIDENCE_THRESHOLD or (
    len(sorted_beliefs) > 1 and
    best_prob / sorted_beliefs[1][1] >= DOMINANCE_RATIO
):

    print("\nPredicted song:")

    for song in songs:
        if song["id"] == best_id:
            print(song["title"])
            print("Confidence:", best_prob)

else:

    print("\nI couldn't confidently identify the song.")
    title = input("What was the song title? ")

    print("\nYou entered:", title)
    print("Consider integrating Wikidata fetch here.")
