#!/usr/bin/env python3
"""
Train Neural Song Embeddings
This script trains the embedding model and saves it for use in the game
"""

import sys
import os

# Add the backend directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.logic.kg_loader import load_dataset
from backend.logic.embeddings import train_embeddings

def main():
    print("🧠 Loading song dataset for embedding training...")
    
    # Load the song dataset
    songs = load_dataset()
    print(f"📊 Loaded {len(songs)} songs")
    
    if len(songs) < 10:
        print("❌ Not enough songs to train embeddings. Need at least 10 songs.")
        return
    
    print("🏋️ Training neural embeddings...")
    print("This will learn semantic relationships between songs...")
    
    try:
        # Train embeddings
        trainer = train_embeddings(songs, epochs=100)
        
        # Save the model
        model_path = os.path.join(os.path.dirname(__file__), 'backend', 'data', 'song_embeddings.pt')
        trainer.save_model(model_path)
        
        print(f"✅ Embeddings trained and saved to {model_path}")
        
        # Show some example similarities
        print("\n🎯 Example similarity results:")
        sample_songs = songs[:5]
        
        for song in sample_songs:
            title = song["title"]
            similar = trainer.find_similar_songs(title, top_k=3)
            if similar:
                print(f"\n{title} is similar to:")
                for similar_title, similarity in similar:
                    print(f"  - {similar_title} ({similarity:.3f})")
        
        print(f"\n🚀 Embedding system ready!")
        print("The game can now use neural similarity instead of fixed tags.")
        
    except Exception as e:
        print(f"❌ Error training embeddings: {e}")
        print("This might be due to insufficient data or installation issues.")
        print("Make sure you have PyTorch installed: pip install torch")

if __name__ == "__main__":
    main()
