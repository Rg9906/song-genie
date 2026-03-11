import json
import os
from typing import Any, Dict, List, Optional

import requests

from backend.logic.config import REQUEST_TIMEOUT_SECONDS


WIKIDATA_SPARQL_URL = "https://query.wikidata.org/sparql"


SPARQL_QUERY = """
SELECT
  ?song ?songLabel
  ?artistLabel
  ?genreLabel
  ?pubDate
  ?languageLabel
  ?countryLabel
  ?awardLabel
  ?labelLabel
  ?producerLabel
  ?composerLabel
  ?partOfLabel
  ?performerLabel
  ?vocalistLabel
  ?filmLabel
  ?tvSeriesLabel
  ?videoGameLabel
  ?billionViews
  ?chartPosition
  ?recordLabelTypeLabel
  ?artistGenderLabel
  ?artistTypeLabel
  ?songTypeLabel
  ?duration
  ?bpm
  ?instrumentLabel
  ?themeLabel
  ?locationLabel
WHERE {
  ?song wdt:P31 wd:Q7366.
  ?song wdt:P175 ?artist.
  ?song wdt:P136 ?genre.
  ?song wdt:P577 ?pubDate.
  ?song wdt:P407 ?language.

  ?song wikibase:sitelinks ?linkCount.
  FILTER(?linkCount > 10)

  # Basic optional fields
  OPTIONAL { ?song wdt:P495 ?country. }
  OPTIONAL { ?song wdt:P166 ?award. }
  OPTIONAL { ?song wdt:P264 ?label. }
  OPTIONAL { ?song wdt:P162 ?producer. }
  OPTIONAL { ?song wdt:P86  ?composer. }
  OPTIONAL { ?song wdt:P361 ?partOf. }

  # Enhanced attributes
  OPTIONAL { ?song wdt:P175 ?performer. ?performer wdt:P21 ?performerGender. }
  OPTIONAL { ?song wdt:P175 ?vocalist. }
  OPTIONAL { ?song wdt:P361 ?film. ?film wdt:P31 wd:Q11424. }  # soundtrack
  OPTIONAL { ?song wdt:P361 ?tvSeries. ?tvSeries wdt:P31 wd:Q15416. }  # TV series
  OPTIONAL { ?song wdt:P361 ?videoGame. ?videoGame wdt:P31 wd:Q7889. }  # video game
  
  # Chart performance
  OPTIONAL { ?song wdt:P432 ?billionViews. FILTER(?billionViews >= 1000000000) }
  OPTIONAL { ?song wdt:P1650 ?chartPosition. }
  
  # Artist details
  OPTIONAL { ?artist wdt:P21 ?artistGender. }
  OPTIONAL { ?artist wdt:P31 ?artistType. }  # solo artist, duo, group
  
  # Song characteristics
  OPTIONAL { ?song wdt:P31 ?songType. }  # single, album track, etc.
  OPTIONAL { ?song wdt:P2047 ?duration. }  # duration in seconds
  OPTIONAL { ?song wdt:P2024 ?bpm. }  # beats per minute
  OPTIONAL { ?song wdt:P828 ?instrument. }  # instruments used
  
  # Thematic and location
  OPTIONAL { ?song wdt:P921 ?theme. }  # main theme
  OPTIONAL { ?song wdt:P276 ?location. }  # location of recording/performance

  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
LIMIT 500
"""


def get_data_path(filename="songs_kg.json"):

    base_dir = os.path.dirname(__file__)

    data_dir = os.path.join(base_dir, "..", "data")

    os.makedirs(data_dir, exist_ok=True)

    return os.path.join(data_dir, filename)


# -------------------------
# Batch Fetch (existing)
# -------------------------

def fetch_songs_from_wikidata() -> Dict[str, Any]:

    headers = {
        "Accept": "application/sparql-results+json"
    }

    try:
        response = requests.get(
            WIKIDATA_SPARQL_URL,
            params={"query": SPARQL_QUERY},
            headers=headers,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        raise RuntimeError("Failed to fetch songs from Wikidata") from exc


# -------------------------
# Single Song Fetch (NEW)
# -------------------------

def _escape_label(label: str) -> str:
    """
    Escape a string for safe use in a SPARQL rdfs:label literal.
    """
    return label.replace("\\", "\\\\").replace('"', '\\"')


def fetch_song_by_title(title: str) -> Optional[Dict[str, Any]]:

    safe_title = _escape_label(title)

    query = f"""
    SELECT ?song ?songLabel ?artistLabel ?genreLabel ?pubDate ?languageLabel ?countryLabel WHERE {{
      ?song wdt:P31 wd:Q7366.
      ?song rdfs:label "{safe_title}"@en.

      OPTIONAL {{ ?song wdt:P175 ?artist. }}
      OPTIONAL {{ ?song wdt:P136 ?genre. }}
      OPTIONAL {{ ?song wdt:P577 ?pubDate. }}
      OPTIONAL {{ ?song wdt:P407 ?language. }}
      OPTIONAL {{ ?song wdt:P495 ?country. }}

      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
    }}
    """

    headers = {
        "Accept": "application/sparql-results+json"
    }

    try:
        response = requests.get(
            WIKIDATA_SPARQL_URL,
            params={"query": query},
            headers=headers,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        data = response.json()
    except (requests.RequestException, ValueError) as exc:
        # ValueError can be raised by response.json()
        raise RuntimeError("Failed to fetch song by title from Wikidata") from exc

    songs = normalize_results(data)

    if len(songs) == 0:
        return None

    return songs[0]


# -------------------------
# Normalization (existing)
# -------------------------

def normalize_results(results: Dict[str, Any]) -> List[Dict[str, Any]]:

    merged: Dict[str, Dict[str, Any]] = {}

    for item in results["results"]["bindings"]:

        title = item.get("songLabel", {}).get("value")
        artist = item.get("artistLabel", {}).get("value")
        genre = item.get("genreLabel", {}).get("value")
        pub_date = item.get("pubDate", {}).get("value")
        language = item.get("languageLabel", {}).get("value")
        country = item.get("countryLabel", {}).get("value")
        award = item.get("awardLabel", {}).get("value")
        label = item.get("labelLabel", {}).get("value")
        producer = item.get("producerLabel", {}).get("value")
        composer = item.get("composerLabel", {}).get("value")
        part_of = item.get("partOfLabel", {}).get("value")
        
        # Enhanced attributes
        performer = item.get("performerLabel", {}).get("value")
        vocalist = item.get("vocalistLabel", {}).get("value")
        film = item.get("filmLabel", {}).get("value")
        tv_series = item.get("tvSeriesLabel", {}).get("value")
        video_game = item.get("videoGameLabel", {}).get("value")
        billion_views = item.get("billionViews", {}).get("value")
        chart_position = item.get("chartPosition", {}).get("value")
        artist_gender = item.get("artistGenderLabel", {}).get("value")
        artist_type = item.get("artistTypeLabel", {}).get("value")
        song_type = item.get("songTypeLabel", {}).get("value")
        duration = item.get("duration", {}).get("value")
        bpm = item.get("bpm", {}).get("value")
        instrument = item.get("instrumentLabel", {}).get("value")
        theme = item.get("themeLabel", {}).get("value")
        location = item.get("locationLabel", {}).get("value")

        if title is None:
            continue

        if title not in merged:

            merged[title] = {

                "title": title,

                "artists": set(),

                "genres": set(),

                "publication_date": pub_date,

                "language": language,

                "country": country,

                # richer, optional attributes
                "awards": set(),

                "labels": set(),

                "producers": set(),

                "composers": set(),

                "part_of": set(),

                # Enhanced attributes
                "performers": set(),
                
                "vocalists": set(),
                
                "films": set(),
                
                "tv_series": set(),
                
                "video_games": set(),
                
                "billion_views": None,
                
                "chart_positions": set(),
                
                "artist_genders": set(),
                
                "artist_types": set(),
                
                "song_types": set(),
                
                "duration": None,
                
                "bpm": None,
                
                "instruments": set(),
                
                "themes": set(),
                
                "locations": set(),

            }

        if artist:
            merged[title]["artists"].add(artist)

        if genre:
            merged[title]["genres"].add(genre)

        if award:
            merged[title]["awards"].add(award)

        if label:
            merged[title]["labels"].add(label)

        if producer:
            merged[title]["producers"].add(producer)

        if composer:
            merged[title]["composers"].add(composer)

        if part_of:
            merged[title]["part_of"].add(part_of)
            
        # Enhanced attributes
        if performer:
            merged[title]["performers"].add(performer)
            
        if vocalist:
            merged[title]["vocalists"].add(vocalist)
            
        if film:
            merged[title]["films"].add(film)
            
        if tv_series:
            merged[title]["tv_series"].add(tv_series)
            
        if video_game:
            merged[title]["video_games"].add(video_game)
            
        if billion_views:
            merged[title]["billion_views"] = int(billion_views)
            
        if chart_position:
            merged[title]["chart_positions"].add(int(chart_position))
            
        if artist_gender:
            merged[title]["artist_genders"].add(artist_gender)
            
        if artist_type:
            merged[title]["artist_types"].add(artist_type)
            
        if song_type:
            merged[title]["song_types"].add(song_type)
            
        if duration:
            merged[title]["duration"] = int(duration)
            
        if bpm:
            merged[title]["bpm"] = int(bpm)
            
        if instrument:
            merged[title]["instruments"].add(instrument)
            
        if theme:
            merged[title]["themes"].add(theme)
            
        if location:
            merged[title]["locations"].add(location)

        if merged[title]["publication_date"] is None and pub_date:
            merged[title]["publication_date"] = pub_date

        if merged[title]["language"] is None and language:
            merged[title]["language"] = language

        if merged[title]["country"] is None and country:
            merged[title]["country"] = country

    songs: List[Dict[str, Any]] = []

    for i, title in enumerate(merged):

        entry = merged[title]

        songs.append({

            "id": i,

            "title": entry["title"],

            "artists": list(entry["artists"]),

            "genres": list(entry["genres"]),

            "publication_date": entry["publication_date"],

            "language": entry["language"],

            "country": entry["country"],

            "awards": list(entry["awards"]),

            "labels": list(entry["labels"]),

            "producers": list(entry["producers"]),

            "composers": list(entry["composers"]),

            "part_of": list(entry["part_of"]),

        })

    return songs


# -------------------------
# Load Existing Dataset
# -------------------------

def load_dataset():

    path = get_data_path()

    if not os.path.exists(path):
        return []

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# -------------------------
# Save Dataset
# -------------------------

def save_dataset(songs):

    path = get_data_path()

    with open(path, "w", encoding="utf-8") as f:
        json.dump(songs, f, indent=2)


# -------------------------
# Append New Song (NEW)
# -------------------------

def append_song(song):

    dataset = load_dataset()

    # check duplicate
    for existing in dataset:

        if existing["title"].lower() == song["title"].lower():

            print("Song already exists in dataset.")

            return False

    new_id = max([s["id"] for s in dataset], default=-1) + 1

    song["id"] = new_id

    dataset.append(song)

    save_dataset(dataset)

    print("Added new song:", song["title"])

    return True


# -------------------------
# Batch Save (existing)
# -------------------------

def save_to_json(songs):

    path = get_data_path()

    with open(path, "w", encoding="utf-8") as f:

        json.dump(songs, f, indent=2)

    print(f"Saved {len(songs)} songs to {path}")


# -------------------------
# Main (existing)
# -------------------------

if __name__ == "__main__":

    print("Fetching songs from Wikidata...")

    raw = fetch_songs_from_wikidata()

    songs = normalize_results(raw)

    save_to_json(songs)

    print("Done.")
