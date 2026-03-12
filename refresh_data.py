#!/usr/bin/env python3
"""
Refresh the song dataset with enhanced attributes from Wikidata.
This will fetch much richer data including:
- Artist gender/type
- Movie/TV/game connections  
- Chart performance
- Musical characteristics
- And much more!
"""

import sys
import os

# Add the backend directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.logic.kg_loader import fetch_songs_from_wikidata, normalize_results, save_to_json

def main():
    print("🎵 Fetching enhanced song data from Wikidata...")
    print("This may take a few minutes as we're fetching much richer data...")
    
    try:
        # Fetch songs with enhanced SPARQL query
        raw_data = fetch_songs_from_wikidata()
        print(f"📊 Fetched {len(raw_data.get('results', {}).get('bindings', []))} raw records")
        
        # Normalize the results
        songs = normalize_results(raw_data)
        print(f"🎯 Normalized to {len(songs)} unique songs")
        
        # Save to JSON
        save_to_json(songs)
        print("✅ Successfully saved enhanced dataset to songs_kg.json")
        
        # Show some examples of enhanced attributes
        print("\n🔍 Sample enhanced attributes:")
        for i, song in enumerate(songs[:3]):
            print(f"\n{i+1}. {song['title']}:")
            for key, value in song.items():
                if key not in ['id', 'title', 'artists', 'genres', 'publication_date', 'language', 'country']:
                    if value and (not isinstance(value, set) or len(value) > 0):
                        print(f"   {key}: {value}")
        
        print(f"\n🚀 Dataset refreshed! You now have {len(songs)} songs with enhanced attributes.")
        print("Restart the backend to use the new data.")
        
    except Exception as e:
        print(f"❌ Error refreshing data: {e}")
        print("This might be due to Wikidata rate limiting. Try again later.")
        sys.exit(1)

if __name__ == "__main__":
    main()
