import json
import os

from backend.logic.belief import initialize_beliefs
from backend.logic.questions import generate_all_questions


class Engine:

    def __init__(self):

        # resolve absolute path safely
        self.data_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "data",
            "songs_kg.json"
        )

        self.entities = []

        self.beliefs = {}

        self.questions = []

        # initial load
        self.load()


    def load(self):
        """
        Loads entities from dataset and initializes
        beliefs and questions.
        """

        with open(self.data_path, "r", encoding="utf-8") as file:

            data = json.load(file)

        entities = []

        for item in data:

            entity = {}

            entity["id"] = item.get("id")

            entity["title"] = item.get("title")

            entity["artists"] = item.get("artists", [])

            entity["genres"] = item.get("genres", [])

            entity["language"] = item.get("language")

            entity["country"] = item.get("country")

            entity["publication_date"] = item.get("publication_date")

            entities.append(entity)

        self.entities = entities

        # initialize beliefs
        self.beliefs = initialize_beliefs(self.entities)

        # generate entropy-optimized questions
        self.questions = generate_all_questions(self.entities)


    def reload(self):
        """
        Reloads dataset after new song is added.
        """

        print("\nReloading knowledge base...")

        self.load()

        print("Reload complete.")

        print("Total entities:", len(self.entities))

        print("Total questions:", len(self.questions))


    def get_entities(self):

        return self.entities


    def get_beliefs(self):

        return self.beliefs


    def get_questions(self):

        return self.questions


    def set_beliefs(self, beliefs):
        """
        Allows external update of belief state.
        """

        self.beliefs = beliefs
