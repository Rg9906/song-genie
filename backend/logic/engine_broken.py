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


            data = json.load(f)

        entities = []

        for idx, item in enumerate(data):

            entity = {"id": idx}

            entity["title"] = item.get("title")

            entity["publication_date"] = item.get("publication_date")

            # Optional richer attributes

            entity["awards"] = item.get("awards", [])

            entity["labels"] = item.get("labels", [])

            entity["producers"] = item.get("producers", [])

            entity["composers"] = item.get("composers", [])

            entity["part_of"] = item.get("part_of", [])

            # Enhanced attributes
            entity["performers"] = item.get("performers", [])
            entity["vocalists"] = item.get("vocalists", [])
            entity["films"] = item.get("films", [])
            entity["tv_series"] = item.get("tv_series", [])
            entity["video_games"] = item.get("video_games", [])
            entity["chart_positions"] = item.get("chart_positions", [])
            entity["artist_genders"] = item.get("artist_genders", [])
            entity["artist_types"] = item.get("artist_types", [])
            entity["song_types"] = item.get("song_types", [])
            entity["duration"] = item.get("duration")
            entity["bpm"] = item.get("bpm")
            entity["instruments"] = item.get("instruments", [])
            entity["themes"] = item.get("themes", [])
            entity["locations"] = item.get("locations", [])

            # Derived, more "graph-like" facts for richer reasoning.
            facts = []

            # Handle list-valued attributes
            for attr in ["artists", "genres", "awards", "labels", "producers", "composers", 
                        "part_of", "performers", "vocalists", "films", "tv_series", 
                        "video_games", "chart_positions", "artist_genders", "artist_types", 
                        "song_types", "instruments", "themes", "locations"]:
                values = item.get(attr, [])
                if not isinstance(values, list):
                    values = [values] if values else []
                entity[attr] = values
                for value in values:
                    facts.append((attr, value))

            # Single-value attributes
            single_attrs = ["language", "country"]
            for attr in single_attrs:
                value = item.get(attr)
                if value:
                    entity[attr] = value
                    facts.append((attr, value))

            # Enhanced attributes facts
            for chart_position in entity["chart_positions"]:
                facts.append(("chart_positions", chart_position))

            # Special numeric facts
            if entity.get("billion_views"):
                facts.append(("billion_views", "yes"))
                
            if entity.get("duration"):
                # Duration categories
                duration = entity["duration"]
                if duration < 120:
                    facts.append(("duration_category", "short"))
                elif duration < 240:
                    facts.append(("duration_category", "medium"))
                else:
                    facts.append(("duration_category", "long"))
                    
            if entity.get("bpm"):
                # BPM categories  
                bpm = entity["bpm"]
                if bpm < 90:
                    facts.append(("bpm_category", "slow"))
                elif bpm < 130:
                    facts.append(("bpm_category", "medium"))
                else:
                    facts.append(("bpm_category", "fast"))

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

        return entities

    def _load_dynamic_graph(self) -> DynamicWikidataGraph:
        """Load or build the dynamic graph."""
        graph = DynamicWikidataGraph()
        
        # Try to load existing graph
        graph_path = os.path.join(os.path.dirname(__file__), "..", "data", "dynamic_graph.json")
        graph.load_graph(graph_path)
        
        # If graph is empty or doesn't exist, build it
        if not graph.graph["songs"]:
            print(" Building dynamic Wikidata graph...")
            graph = build_dynamic_graph(limit=200)  # Start with 200 songs
            graph.save_graph(graph_path)
        
        return graph

    def _enhance_with_dynamic_graph(self):
        """Enhance entities with dynamic graph attributes."""
        if not self.dynamic_graph:
            return
        
        enhanced_entities = []
        
        for entity in self.entities:
            song_title = entity["title"]
            
            # Get dynamic attributes for this song
            dynamic_attrs = self.dynamic_graph.get_song_attributes(song_title)
            
            # Merge dynamic attributes
            for attr_type, value in dynamic_attrs.items():
                if attr_type not in entity:
                    entity[attr_type] = value if not isinstance(value, list) else [value]
                    entity["facts"].append((attr_type, value))
            
            enhanced_entities.append(entity)
        
        self.entities = enhanced_entities

    def _initialize_beliefs(self) -> List[float]:

        return initialize_beliefs(self.entities)

    def _generate_questions(self) -> List[Dict[str, Any]]:

        return generate_all_questions(self.entities)

    def get_entities(self) -> List[Dict[str, Any]]:

        return self.entities

    def get_beliefs(self) -> List[float]:

    def get_beliefs(self):

        return self.beliefs


    def get_questions(self):

        return self.questions


    def set_beliefs(self, beliefs):
        """
        Allows external update of belief state.
        """

        self.beliefs = beliefs
