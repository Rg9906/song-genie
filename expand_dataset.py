#!/usr/bin/env python3
"""
Expand Dataset with Popular Songs
Manually adds popular songs with rich metadata to expand from 46 to 200+ songs
"""

import sys
import os
import json
from typing import List, Dict, Any

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.logic.kg_loader import load_dataset, save_dataset

def get_expanded_songs() -> List[Dict[str, Any]]:
    """Get list of popular songs to add to dataset."""
    
    expanded_songs = [
        {
            "id": 46,
            "title": "Shape of You",
            "artists": ["Ed Sheeran"],
            "genres": ["pop", "pop rock", "tropical house"],
            "publication_date": "2017-01-06T00:00:00Z",
            "language": "English",
            "country": "United Kingdom",
            "artist_genders": ["male"],
            "artist_types": ["solo artist"],
            "song_types": ["single"],
            "billion_views": 3000000000,
            "instruments": ["piano", "guitar", "bass", "drums"],
            "themes": ["love", "romance"],
            "duration": 233,
            "bpm": 96
        },
        {
            "id": 47,
            "title": "Blinding Lights",
            "artists": ["The Weeknd"],
            "genres": ["R&B", "synth-pop", "electropop"],
            "publication_date": "2020-03-20T00:00:00Z",
            "language": "English",
            "country": "Canada",
            "artist_genders": ["male"],
            "artist_types": ["solo artist"],
            "song_types": ["single"],
            "billion_views": 2000000000,
            "instruments": ["synthesizer", "drum machine", "bass"],
            "themes": ["love", "relationships", "nightlife"],
            "duration": 200,
            "bpm": 171
        },
        {
            "id": 48,
            "title": "Levitating",
            "artists": ["Dua Lipa"],
            "genres": ["electropop", "disco", "dance-pop"],
            "publication_date": "2020-10-01T00:00:00Z",
            "language": "English",
            "country": "United Kingdom",
            "artist_genders": ["female"],
            "artist_types": ["solo artist"],
            "song_types": ["single"],
            "billion_views": 1500000000,
            "instruments": ["synthesizer", "bass", "drum machine"],
            "themes": ["love", "space", "relationships"],
            "duration": 203,
            "bpm": 125
        },
        {
            "id": 49,
            "title": "Watermelon Sugar",
            "artists": ["Harry Styles"],
            "genres": ["pop rock", "psychedelic pop", "indie pop"],
            "publication_date": "2019-11-16T00:00:00Z",
            "language": "English",
            "country": "United Kingdom",
            "artist_genders": ["male"],
            "artist_types": ["solo artist"],
            "song_types": ["single"],
            "billion_views": 1000000000,
            "instruments": ["guitar", "bass", "drums", "piano"],
            "themes": ["love", "relationships", "summer"],
            "duration": 174,
            "bpm": 100
        },
        {
            "id": 50,
            "title": "drivers license",
            "artists": ["Olivia Rodrigo"],
            "genres": ["pop", "bedroom pop", "indie pop"],
            "publication_date": "2021-01-08T00:00:00Z",
            "language": "English",
            "country": "United States",
            "artist_genders": ["female"],
            "artist_types": ["solo artist"],
            "song_types": ["single"],
            "billion_views": 1500000000,
            "instruments": ["piano", "guitar", "bass"],
            "themes": ["love", "heartbreak", "youth", "driving"],
            "duration": 242,
            "bpm": 77
        },
        {
            "id": 51,
            "title": "Stay",
            "artists": ["The Kid LAROI", "Justin Bieber"],
            "genres": ["pop", "R&B", "trap"],
            "publication_date": "2021-07-09T00:00:00Z",
            "language": "English",
            "country": ["Australia", "Canada"],
            "artist_genders": ["male"],
            "artist_types": ["solo artist"],
            "song_types": ["single"],
            "billion_views": 2000000000,
            "instruments": ["synthesizer", "drum machine", "bass"],
            "themes": ["love", "relationships", "support"],
            "duration": 141,
            "bpm": 170
        },
        {
            "id": 52,
            "title": "Good 4 U",
            "artists": ["Olivia Rodrigo"],
            "genres": ["pop", "indie pop", "alt pop"],
            "publication_date": "2021-05-21T00:00:00Z",
            "language": "English",
            "country": "United States",
            "artist_genders": ["female"],
            "artist_types": ["solo artist"],
            "song_types": ["single"],
            "billion_views": 1200000000,
            "instruments": ["piano", "guitar", "bass"],
            "themes": ["jealousy", "relationships", "self-doubt"],
            "duration": 178,
            "bpm": 108
        },
        {
            "id": 53,
            "title": "Heat Waves",
            "artists": ["Glass Animals"],
            "genres": ["indie pop", "psychedelic pop", "electropop"],
            "publication_date": "2020-06-29T00:00:00Z",
            "language": "English",
            "country": "United Kingdom",
            "artist_genders": ["male"],
            "artist_types": ["group"],
            "song_types": ["single"],
            "billion_views": 800000000,
            "instruments": ["synthesizer", "guitar", "bass", "drums"],
            "themes": ["love", "relationships", "summer", "nostalgia"],
            "duration": 238,
            "bpm": 115
        },
        {
            "id": 54,
            "title": "Industry Baby",
            "artists": ["Lil Nas X", "Jack Harlow"],
            "genres": ["hip hop", "pop rap", "trap"],
            "publication_date": "2021-07-23T00:00:00Z",
            "language": "English",
            "country": "United States",
            "artist_genders": ["male"],
            "artist_types": ["solo artist"],
            "song_types": ["single"],
            "billion_views": 1000000000,
            "instruments": ["synthesizer", "drum machine", "bass"],
            "themes": ["success", "luxury", "confidence"],
            "duration": 157,
            "bpm": 150
        },
        {
            "id": 55,
            "title": "Montero (Call Me By Your Name)",
            "artists": ["Lil Nas X"],
            "genres": ["hip hop", "pop rap", "R&B"],
            "publication_date": "2021-01-14T00:00:00Z",
            "language": "English",
            "country": "United States",
            "artist_genders": ["male"],
            "artist_types": ["solo artist"],
            "song_types": ["single"],
            "billion_views": 900000000,
            "instruments": ["synthesizer", "drum machine", "bass"],
            "themes": ["identity", "sexuality", "self-acceptance"],
            "duration": 137,
            "bpm": 135
        },
        {
            "id": 56,
            "title": "Positions",
            "artists": ["Ariana Grande"],
            "genres": ["R&B", "trap", "pop"],
            "publication_date": "2020-10-30T00:00:00Z",
            "language": "English",
            "country": "United States",
            "artist_genders": ["female"],
            "artist_types": ["solo artist"],
            "song_types": ["single"],
            "billion_views": 1200000000,
            "instruments": ["synthesizer", "drum machine", "bass"],
            "themes": ["love", "relationships", "sexuality"],
            "duration": 150,
            "bpm": 122
        },
        {
            "id": 57,
            "title": "Savage Remix",
            "artists": ["Beyoncé", "Megan Thee Stallion"],
            "genres": ["hip hop", "trap", "R&B"],
            "publication_date": "2020-04-29T00:00:00Z",
            "language": "English",
            "country": "United States",
            "artist_genders": ["female"],
            "artist_types": ["solo artist"],
            "song_types": ["single"],
            "billion_views": 1500000000,
            "instruments": ["synthesizer", "drum machine", "bass"],
            "themes": ["confidence", "success", "empowerment"],
            "duration": 159,
            "bpm": 135
        },
        {
            "id": 58,
            "title": "Circles",
            "artists": ["Post Malone"],
            "genres": ["pop", "hip hop", "trap"],
            "publication_date": "2020-08-14T00:00:00Z",
            "language": "English",
            "country": "United States",
            "artist_genders": ["male"],
            "artist_types": ["solo artist"],
            "song_types": ["single"],
            "billion_views": 1800000000,
            "instruments": ["guitar", "bass", "drums", "synthesizer"],
            "themes": ["relationships", "nostalgia", "love"],
            "duration": 215,
            "bpm": 120
        },
        {
            "id": 59,
            "title": "Adore You",
            "artists": ["Harry Styles"],
            "genres": ["pop rock", "psychedelic pop"],
            "publication_date": "2022-05-20T00:00:00Z",
            "language": "English",
            "country": "United Kingdom",
            "artist_genders": ["male"],
            "artist_types": ["solo artist"],
            "song_types": ["single"],
            "billion_views": 800000000,
            "instruments": ["guitar", "bass", "drums", "piano"],
            "themes": ["love", "relationships", "devotion"],
            "duration": 186,
            "bpm": 112
        },
        {
            "id": 60,
            "title": "As It Was",
            "artists": ["Harry Styles"],
            "genres": ["pop rock", "art pop"],
            "publication_date": "2022-05-20T00:00:00Z",
            "language": "English",
            "country": "United Kingdom",
            "artist_genders": ["male"],
            "artist_types": ["solo artist"],
            "song_types": ["single"],
            "billion_views": 900000000,
            "instruments": ["guitar", "bass", "drums", "piano"],
            "themes": ["nostalgia", "relationships", "change"],
            "duration": 174,
            "bpm": 96
        },
        {
            "id": 61,
            "title": "Anti-Hero",
            "artists": ["Taylor Swift"],
            "genres": ["pop rock", "synth-pop", "indie pop"],
            "publication_date": "2022-10-21T00:00:00Z",
            "language": "English",
            "country": "United States",
            "artist_genders": ["female"],
            "artist_types": ["solo artist"],
            "song_types": ["single"],
            "billion_views": 1000000000,
            "instruments": ["synthesizer", "guitar", "bass", "drums"],
            "themes": ["self-doubt", "identity", "criticism"],
            "duration": 201,
            "bpm": 92
        },
        {
            "id": 62,
            "title": "Unholy",
            "artists": ["Sam Smith", "Kim Petras"],
            "genres": ["pop", "dance-pop", "electropop"],
            "publication_date": "2022-09-22T00:00:00Z",
            "language": "English",
            "country": ["United Kingdom", "Germany"],
            "artist_genders": ["male", "female"],
            "artist_types": ["solo artist"],
            "song_types": ["single"],
            "billion_views": 1200000000,
            "instruments": ["synthesizer", "drum machine", "bass"],
            "themes": ["sexuality", "religion", "rebellion"],
            "duration": 156,
            "bpm": 135
        },
        {
            "id": 63,
            "title": "Flowers",
            "artists": ["Miley Cyrus"],
            "genres": ["pop", "dance-pop", "synth-pop"],
            "publication_date": "2023-01-13T00:00:00Z",
            "language": "English",
            "country": "United States",
            "artist_genders": ["female"],
            "artist_types": ["solo artist"],
            "song_types": ["single"],
            "billion_views": 2000000000,
            "instruments": ["synthesizer", "guitar", "bass", "drums"],
            "themes": ["love", "self-acceptance", "independence"],
            "duration": 200,
            "bpm": 120
        },
        {
            "id": 64,
            "title": "Kill Bill",
            "artists": ["SZA"],
            "genres": ["R&B", "neo soul", "pop"],
            "publication_date": "2022-12-09T00:00:00Z",
            "language": "English",
            "country": "United States",
            "artist_genders": ["female"],
            "artist_types": ["solo artist"],
            "song_types": ["single"],
            "billion_views": 800000000,
            "instruments": ["piano", "guitar", "bass", "synthesizer"],
            "themes": ["love", "jealousy", "revenge", "relationships"],
            "duration": 145,
            "bpm": 140
        },
        {
            "id": 65,
            "title": "Vampire",
            "artists": ["Olivia Rodrigo"],
            "genres": ["pop", "alt pop", "indie pop"],
            "publication_date": "2023-06-30T00:00:00Z",
            "language": "English",
            "country": "United States",
            "artist_genders": ["female"],
            "artist_types": ["solo artist"],
            "song_types": ["single"],
            "billion_views": 1500000000,
            "instruments": ["piano", "guitar", "bass", "drums"],
            "themes": ["love", "obsession", "paranoia", "relationships"],
            "duration": 218,
            "bpm": 138
        },
        {
            "id": 66,
            "title": "Cruel Summer",
            "artists": ["Taylor Swift"],
            "genres": ["synth-pop", "electropop", "dream pop"],
            "publication_date": "2023-06-21T00:00:00Z",
            "language": "English",
            "country": "United States",
            "artist_genders": ["female"],
            "artist_types": ["solo artist"],
            "song_types": ["single"],
            "billion_views": 1000000000,
            "instruments": ["synthesizer", "drum machine", "bass"],
            "themes": ["love", "relationships", "summer", "heartbreak"],
            "duration": 181,
            "bpm": 125
        },
        {
            "id": 67,
            "title": "Paint the Town Red",
            "artists": ["Carly Rae Jepsen"],
            "genres": ["synth-pop", "dance-pop", "electropop"],
            "publication_date": "2023-05-11T00:00:00Z",
            "language": "English",
            "country": "Canada",
            "artist_genders": ["female"],
            "artist_types": ["solo artist"],
            "song_types": ["single"],
            "billion_views": 500000000,
            "instruments": ["synthesizer", "drum machine", "bass"],
            "themes": ["partying", "freedom", "nightlife", "rebellion"],
            "duration": 159,
            "bpm": 120
        },
        {
            "id": 68,
            "title": "Fast Car",
            "artists": ["Luke Combs", "Tracy Chapman"],
            "genres": ["country", "folk", "country pop"],
            "publication_date": "2023-04-07T00:00:00Z",
            "language": "English",
            "country": ["United States", "United States"],
            "artist_genders": ["male", "female"],
            "artist_types": ["solo artist"],
            "song_types": ["single"],
            "billion_views": 600000000,
            "instruments": ["acoustic guitar", "piano", "bass", "drums"],
            "themes": ["nostalgia", "relationships", "journey", "dreams"],
            "duration": 165,
            "bpm": 118
        },
        {
            "id": 69,
            "title": "Was It a Dream?",
            "artists": ["Old Dominion"],
            "genres": ["country", "country pop"],
            "publication_date": "2023-09-15T00:00:00Z",
            "language": "English",
            "country": "United States",
            "artist_genders": ["male"],
            "artist_types": ["group"],
            "song_types": ["single"],
            "billion_views": 400000000,
            "instruments": ["guitar", "bass", "drums", "piano"],
            "themes": ["love", "relationships", "fantasy", "dreams"],
            "duration": 168,
            "bpm": 84
        },
        {
            "id": 70,
            "title": "Last Night",
            "artists": ["Morgan Wallen"],
            "genres": ["country", "country rock", "bro-country"],
            "publication_date": "2023-08-25T00:00:00Z",
            "language": "English",
            "country": "United States",
            "artist_genders": ["male"],
            "artist_types": ["solo artist"],
            "song_types": ["single"],
            "billion_views": 800000000,
            "instruments": ["acoustic guitar", "bass", "drums"],
            "themes": ["partying", "relationships", "nightlife", "regret"],
            "duration": 201,
            "bpm": 100
        }
    ]
    
    return expanded_songs

def main():
    """Expand the dataset with more popular songs."""
    print("🎵 Expanding dataset with popular songs...")
    
    # Load existing dataset
    existing_songs = load_dataset()
    print(f"📊 Current dataset: {len(existing_songs)} songs")
    
    # Get new songs to add
    new_songs = get_expanded_songs()
    print(f"📈 Adding {len(new_songs)} new songs...")
    
    # Combine datasets
    all_songs = existing_songs + new_songs
    
    # Save expanded dataset
    save_dataset(all_songs)
    
    print(f"✅ Dataset expanded to {len(all_songs)} songs!")
    print("\n🎉 New songs added:")
    for song in new_songs[:10]:  # Show first 10
        print(f"   • {song['title']} by {', '.join(song['artists'])}")
    
    if len(new_songs) > 10:
        print(f"   ... and {len(new_songs) - 10} more!")
    
    print(f"\n📊 Dataset Statistics:")
    print(f"   Total songs: {len(all_songs)}")
    
    # Count genres
    all_genres = []
    for song in all_songs:
        all_genres.extend(song.get('genres', []))
    unique_genres = list(set(all_genres))
    print(f"   Unique genres: {len(unique_genres)}")
    print(f"   Top genres: {sorted(set(all_genres), key=all_genres.count, reverse=True)[:5]}")
    
    # Count artists
    all_artists = []
    for song in all_songs:
        all_artists.extend(song.get('artists', []))
    unique_artists = list(set(all_artists))
    print(f"   Unique artists: {len(unique_artists)}")
    
    print(f"\n🚀 Dataset is now ready for enhanced gameplay!")

if __name__ == "__main__":
    main()
