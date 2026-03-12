"""
Dynamic Wikidata Graph System
Builds a massive interconnected graph where:
- Songs are nodes
- Every unique attribute from Wikidata becomes a node
- Edges connect songs to their attribute nodes
- Attribute nodes connect to all songs sharing that attribute
"""

import json
import requests
from typing import Dict, List, Any, Set, Tuple
from collections import defaultdict, Counter
import os

from backend.logic.config import WIKIDATA_SPARQL_URL, REQUEST_TIMEOUT_SECONDS


class DynamicWikidataGraph:
    def __init__(self):
        self.graph = {
            "songs": {},  # song_id -> song_data + edges
            "attributes": {},  # attribute_key -> {value: set of song_ids}
            "attribute_types": set()  # all unique attribute types discovered
        }
    
    def discover_all_attributes(self, limit: int = 500) -> List[Dict[str, Any]]:
        """
        Discover ALL possible attributes from Wikidata songs, not just predefined ones.
        Uses a much broader SPARQL query to find any property connected to songs.
        """
        
        # Ultra-comprehensive SPARQL query to get ALL properties
        comprehensive_query = """
        SELECT DISTINCT ?song ?songLabel ?property ?propertyLabel ?value ?valueLabel WHERE {
          ?song wdt:P31 wd:Q7366.  # is a song
          ?song ?property ?value.
          
          # Filter out some less useful properties
          FILTER(?property NOT IN (wdt:P143, wdt:P4656, wdt:P1476, wdt:P123, wdt:P971))
          
          # Only get properties that have labels
          ?property rdfs:label ?propertyLabel.
          FILTER(LANG(?propertyLabel) = "en")
          
          # Try to get value labels
          OPTIONAL {
            ?value rdfs:label ?valueLabel.
            FILTER(LANG(?valueLabel) = "en")
          }
          
          ?song rdfs:label ?songLabel.
          FILTER(LANG(?songLabel) = "en")
          
          # Basic popularity filter
          ?song wikibase:sitelinks ?linkCount.
          FILTER(?linkCount > 5)
        }
        LIMIT """ + str(limit)
        
        headers = {
            "Accept": "application/sparql-results+json",
            "User-Agent": "MusicGenie/1.0 (Educational)"
        }
        
        try:
            response = requests.get(
                WIKIDATA_SPARQL_URL,
                params={"query": comprehensive_query},
                headers=headers,
                timeout=REQUEST_TIMEOUT_SECONDS
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching comprehensive data: {e}")
            return {"results": {"bindings": []}}
    
    def build_graph_from_wikidata(self, raw_data: Dict[str, Any]) -> None:
        """
        Build the dynamic graph from comprehensive Wikidata data.
        """
        bindings = raw_data.get("results", {}).get("bindings", [])
        
        # Track all attributes we discover
        discovered_attributes = defaultdict(lambda: defaultdict(set))
        song_data = defaultdict(dict)
        
        for binding in bindings:
            song_uri = binding.get("song", {}).get("value", "")
            song_label = binding.get("songLabel", {}).get("value", "")
            prop_uri = binding.get("property", {}).get("value", "")
            prop_label = binding.get("propertyLabel", {}).get("value", "")
            value_uri = binding.get("value", {}).get("value", "")
            value_label = binding.get("valueLabel", {}).get("value", "")
            
            if not song_label or not prop_label:
                continue
            
            # Extract Wikidata property ID (e.g., "P175" from "http://www.wikidata.org/entity/P175")
            prop_id = prop_uri.split("/")[-1] if "/" in prop_uri else prop_label
            
            # Use value label if available, otherwise use URI
            value_display = value_label if value_label else value_uri
            
            # Store attribute
            discovered_attributes[prop_label][value_display].add(song_label)
            
            # Store basic song info
            if "title" not in song_data[song_label]:
                song_data[song_label]["title"] = song_label
                song_data[song_label]["attributes"] = {}
            
            song_data[song_label]["attributes"][prop_label] = value_display
            
            # Track attribute types
            self.attribute_types.add(prop_label)
        
        # Build the final graph structure
        self.graph["attributes"] = {
            attr_type: dict(values) 
            for attr_type, values in discovered_attributes.items()
        }
        
        self.graph["songs"] = dict(song_data)
        
        print(f"🌐 Built dynamic graph:")
        print(f"   Songs: {len(self.graph['songs'])}")
        print(f"   Attribute types: {len(self.graph['attributes'])}")
        print(f"   Total attribute nodes: {sum(len(values) for values in self.graph['attributes'].values())}")
    
    def get_connected_songs(self, attribute: str, value: str) -> Set[str]:
        """
        Get all songs connected to a specific attribute value.
        """
        return self.graph["attributes"].get(attribute, {}).get(value, set())
    
    def get_song_attributes(self, song_title: str) -> Dict[str, str]:
        """
        Get all attributes for a specific song.
        """
        return self.graph["songs"].get(song_title, {}).get("attributes", {})
    
    def find_common_attributes(self, songs: List[str]) -> Dict[str, Dict[str, float]]:
        """
        Find attributes that are common among a group of songs.
        Returns: {attribute_type: {value: coverage_percentage}}
        """
        if not songs:
            return {}
        
        common_attrs = defaultdict(lambda: defaultdict(int))
        
        for song in songs:
            attrs = self.get_song_attributes(song)
            for attr_type, value in attrs.items():
                common_attrs[attr_type][value] += 1
        
        # Convert to percentages
        result = {}
        for attr_type, values in common_attrs.items():
            result[attr_type] = {
                value: count / len(songs) 
                for value, count in values.items()
            }
        
        return result
    
    def get_distinguishing_attributes(self, song: str, other_songs: List[str]) -> Dict[str, float]:
        """
        Find attributes that distinguish a song from others.
        Returns: {attribute_value: distinguishing_score}
        """
        song_attrs = self.get_song_attributes(song)
        distinguishing = {}
        
        for attr_type, value in song_attrs.items():
            songs_with_attr = self.get_connected_songs(attr_type, value)
            
            # Calculate distinguishing score (lower = more distinguishing)
            overlap = len(songs_with_attr.intersection(set(other_songs)))
            score = overlap / len(other_songs) if other_songs else 0
            
            distinguishing[f"{attr_type}:{value}"] = 1.0 - score
        
        return distinguishing
    
    def generate_smart_questions(self, candidate_songs: List[str], asked_questions: Set[Tuple[str, str]]) -> List[Dict[str, Any]]:
        """
        Generate smart questions based on the dynamic graph.
        """
        if len(candidate_songs) <= 1:
            return []
        
        questions = []
        
        # Find distinguishing attributes
        for song in candidate_songs[:5]:  # Check top candidates
            other_songs = [s for s in candidate_songs if s != song]
            distinguishing = self.get_distinguishing_attributes(song, other_songs)
            
            for attr_value, score in distinguishing.items():
                if score > 0.3:  # Only consider reasonably distinguishing attributes
                    attr_type, value = attr_value.split(":", 1)
                    key = (attr_type, value)
                    
                    if key not in asked_questions:
                        questions.append({
                            "feature": attr_type,
                            "value": value,
                            "distinguishing_score": score,
                            "covers_songs": len(self.get_connected_songs(attr_type, value))
                        })
        
        # Sort by distinguishing score
        questions.sort(key=lambda q: q["distinguishing_score"], reverse=True)
        
        return questions[:20]  # Return top 20 questions
    
    def save_graph(self, filepath: str) -> None:
        """Save the graph to file."""
        # Convert sets to lists for JSON serialization
        serializable_graph = {
            "songs": self.graph["songs"],
            "attributes": {
                attr_type: {
                    value: list(song_set) 
                    for value, song_set in values.items()
                }
                for attr_type, values in self.graph["attributes"].items()
            },
            "attribute_types": list(self.attribute_types)
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(serializable_graph, f, indent=2, ensure_ascii=False)
    
    def load_graph(self, filepath: str) -> None:
        """Load the graph from file."""
        if not os.path.exists(filepath):
            return
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Convert lists back to sets
        self.graph["songs"] = data.get("songs", {})
        self.graph["attributes"] = {
            attr_type: {
                value: set(song_list) 
                for value, song_list in values.items()
            }
            for attr_type, values in data.get("attributes", {}).items()
        }
        self.attribute_types = set(data.get("attribute_types", []))


def build_dynamic_graph(limit: int = 500) -> DynamicWikidataGraph:
    """
    Build a comprehensive dynamic graph from Wikidata.
    """
    graph = DynamicWikidataGraph()
    
    print("🔍 Discovering all attributes from Wikidata...")
    raw_data = graph.discover_all_attributes(limit)
    
    print("🏗️ Building dynamic graph...")
    graph.build_graph_from_wikidata(raw_data)
    
    return graph
