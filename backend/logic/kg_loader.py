import requests
import json
import os


WIKIDATA_SPARQL_URL = "https://query.wikidata.org/sparql"


SPARQL_QUERY = """
SELECT ?song ?songLabel ?artistLabel ?genreLabel ?pubDate ?languageLabel ?countryLabel WHERE {
  ?song wdt:P31 wd:Q7366.
  ?song wdt:P175 ?artist.
  ?song wdt:P136 ?genre.
  ?song wdt:P577 ?pubDate.
  ?song wdt:P407 ?language.

  ?song wikibase:sitelinks ?linkCount.
  FILTER(?linkCount > 15)

  OPTIONAL { ?song wdt:P495 ?country. }

  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
LIMIT 100
"""


def get_data_path(filename="songs_kg.json"):

    base_dir = os.path.dirname(__file__)

    data_dir = os.path.join(base_dir, "..", "data")

    os.makedirs(data_dir, exist_ok=True)

    return os.path.join(data_dir, filename)


# -------------------------
# Batch Fetch (existing)
# -------------------------

def fetch_songs_from_wikidata():

    headers = {
        "Accept": "application/sparql-results+json"
    }

    response = requests.get(
        WIKIDATA_SPARQL_URL,
        params={"query": SPARQL_QUERY},
        headers=headers
    )

    response.raise_for_status()

    return response.json()


# -------------------------
# Single Song Fetch (NEW)
# -------------------------

def fetch_song_by_title(title):

    query = f"""
    SELECT ?song ?songLabel ?artistLabel ?genreLabel ?pubDate ?languageLabel ?countryLabel WHERE {{
      ?song wdt:P31 wd:Q7366.
      ?song rdfs:label "{title}"@en.

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

    response = requests.get(
        WIKIDATA_SPARQL_URL,
        params={"query": query},
        headers=headers
    )

    response.raise_for_status()

    data = response.json()

    songs = normalize_results(data)

    if len(songs) == 0:
        return None

    return songs[0]


# -------------------------
# Normalization (existing)
# -------------------------

def normalize_results(results):

    merged = {}

    for item in results["results"]["bindings"]:

        title = item.get("songLabel", {}).get("value")
        artist = item.get("artistLabel", {}).get("value")
        genre = item.get("genreLabel", {}).get("value")
        pub_date = item.get("pubDate", {}).get("value")
        language = item.get("languageLabel", {}).get("value")
        country = item.get("countryLabel", {}).get("value")

        if title is None:
            continue

        if title not in merged:

            merged[title] = {

                "title": title,

                "artists": set(),

                "genres": set(),

                "publication_date": pub_date,

                "language": language,

                "country": country

            }

        if artist:
            merged[title]["artists"].add(artist)

        if genre:
            merged[title]["genres"].add(genre)

        if merged[title]["publication_date"] is None and pub_date:
            merged[title]["publication_date"] = pub_date

        if merged[title]["language"] is None and language:
            merged[title]["language"] = language

        if merged[title]["country"] is None and country:
            merged[title]["country"] = country

    songs = []

    for i, title in enumerate(merged):

        entry = merged[title]

        songs.append({

            "id": i,

            "title": entry["title"],

            "artists": list(entry["artists"]),

            "genres": list(entry["genres"]),

            "publication_date": entry["publication_date"],

            "language": entry["language"],

            "country": entry["country"]

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
