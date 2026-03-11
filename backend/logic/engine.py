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

            # Core attributes from the dataset
            entity["artists"] = item.get("artists", [])

            entity["genres"] = item.get("genres", [])

            entity["language"] = item.get("language")

            entity["country"] = item.get("country")

            entity["publication_date"] = item.get("publication_date")

            # Optional richer attributes
            entity["awards"] = item.get("awards", [])
            entity["labels"] = item.get("labels", [])
            entity["producers"] = item.get("producers", [])
            entity["composers"] = item.get("composers", [])
            entity["part_of"] = item.get("part_of", [])

            # Derived, more "graph-like" facts for richer reasoning.
            facts = []

            for artist in entity["artists"]:
                facts.append(("artists", artist))

            for genre in entity["genres"]:
                facts.append(("genres", genre))

            if entity["language"]:
                facts.append(("language", entity["language"]))

            if entity["country"]:
                facts.append(("country", entity["country"]))

            for award in entity["awards"]:
                facts.append(("awards", award))

            for label in entity["labels"]:
                facts.append(("labels", label))

            for producer in entity["producers"]:
                facts.append(("producers", producer))

            for composer in entity["composers"]:
                facts.append(("composers", composer))

            for part in entity["part_of"]:
                facts.append(("part_of", part))

            pub_date = entity["publication_date"]
            year = None
            if isinstance(pub_date, str) and len(pub_date) >= 4:
                try:
                    year = int(pub_date[:4])
                except ValueError:
                    year = None

            if year is not None:
                # Store numeric year and coarse era / decade buckets.
                entity["year"] = year
                facts.append(("year", year))

                decade_start = (year // 10) * 10
                decade_label = f"{decade_start}s"
                entity["decade"] = decade_label
                facts.append(("decade", decade_label))

                if year < 2000:
                    era = "Before_2000"
                elif 2000 <= year < 2010:
                    era = "2000_2010"
                elif 2010 <= year < 2020:
                    era = "2010_2020"
                else:
                    era = "After_2020"
                entity["era"] = era
                facts.append(("era", era))

            entity["facts"] = facts

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
