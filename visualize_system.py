#!/usr/bin/env python3
"""
System Visualization Tool
Simple visualization of song clusters and graph structure
"""

import sys
import os
import json
import matplotlib.pyplot as plt
import numpy as np
from typing import List, Dict, Any, Optional

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.logic.hybrid_engine import create_hybrid_engine
from backend.logic.kg_loader import load_dataset

def visualize_song_clusters():
    """Visualize song clusters using available metadata."""
    print("🎨 Visualizing Song Clusters...")
    
    # Load songs
    songs = load_dataset()
    if len(songs) < 2:
        print("❌ Need at least 2 songs for visualization")
        return
    
    # Create feature vectors from metadata
    features = []
    song_titles = []
    
    for song in songs:
        feature_vector = extract_features(song)
        if feature_vector is not None:
            features.append(feature_vector)
            song_titles.append(song['title'])
    
    if len(features) < 2:
        print("❌ Not enough valid songs for visualization")
        return
    
    features = np.array(features)
    
    # Simple 2D projection using first two principal components
    # (Simplified - not using sklearn to avoid dependency)
    centered_features = features - np.mean(features, axis=0)
    
    # Calculate covariance matrix
    cov_matrix = np.cov(centered_features.T)
    
    # Get eigenvalues and eigenvectors
    eigenvalues, eigenvectors = np.linalg.eigh(cov_matrix)
    
    # Sort by eigenvalue (descending)
    idx = np.argsort(eigenvalues)[::-1]
    eigenvectors = eigenvectors[:, idx]
    
    # Project to 2D using top 2 eigenvectors
    projected = centered_features @ eigenvectors[:, :2]
    
    # Create visualization
    plt.figure(figsize=(12, 8))
    
    # Plot songs
    for i, (x, y) in enumerate(projected):
        plt.scatter(x, y, alpha=0.7, s=100)
        plt.annotate(song_titles[i], (x, y), fontsize=8, alpha=0.8)
    
    plt.title('Song Clusters (Metadata-based 2D Projection)')
    plt.xlabel('Principal Component 1')
    plt.ylabel('Principal Component 2')
    plt.grid(True, alpha=0.3)
    
    # Save plot
    plt.tight_layout()
    plt.savefig('song_clusters.png', dpi=150, bbox_inches='tight')
    print("✅ Saved visualization to 'song_clusters.png'")
    
    # Show some statistics
    print(f"📊 Visualization Statistics:")
    print(f"   Songs plotted: {len(song_titles)}")
    print(f"   Feature dimensions: {features.shape[1]}")
    print(f"   Variance explained (PC1): {eigenvalues[0] / eigenvalues.sum():.3f}")
    print(f"   Variance explained (PC2): {eigenvalues[1] / eigenvalues.sum():.3f}")

def extract_features(song: Dict[str, Any]) -> Optional[np.ndarray]:
    """Extract numerical features from song metadata."""
    try:
        features = []
        
        # Basic features
        features.append(len(song.get('title', '')))  # Title length
        features.append(len(song.get('artists', [])))  # Number of artists
        features.append(len(song.get('genres', [])))  # Number of genres
        
        # Year feature (if available)
        pub_date = song.get('publication_date', '')
        if pub_date and len(pub_date) >= 4:
            try:
                year = int(pub_date[:4])
                features.append(year - 2000)  # Years since 2000
            except ValueError:
                features.append(0)
        else:
            features.append(0)
        
        # Binary features for common attributes
        features.append(1 if 'female' in str(song.get('artist_genders', [])) else 0)
        features.append(1 if 'solo artist' in str(song.get('artist_types', [])) else 0)
        features.append(1 if 'single' in str(song.get('song_types', [])) else 0)
        features.append(1 if song.get('billion_views') else 0)
        
        # Genre features (one-hot for common genres)
        common_genres = ['pop', 'rock', 'electronic', 'hip-hop', 'jazz', 'classical']
        genres = [g.lower() for g in song.get('genres', [])]
        for genre in common_genres:
            features.append(1 if any(genre in g for g in genres) else 0)
        
        return np.array(features, dtype=float)
        
    except Exception as e:
        print(f"Warning: Could not extract features for {song.get('title', 'Unknown')}: {e}")
        return None

def visualize_genre_distribution():
    """Visualize genre distribution."""
    print("🎵 Visualizing Genre Distribution...")
    
    songs = load_dataset()
    
    # Count genres
    genre_counts = {}
    for song in songs:
        genres = song.get('genres', [])
        for genre in genres:
            genre_counts[genre] = genre_counts.get(genre, 0) + 1
    
    if not genre_counts:
        print("❌ No genre data found")
        return
    
    # Create visualization
    plt.figure(figsize=(12, 6))
    
    genres = list(genre_counts.keys())
    counts = list(genre_counts.values())
    
    plt.bar(genres, counts)
    plt.title('Genre Distribution')
    plt.xlabel('Genre')
    plt.ylabel('Number of Songs')
    plt.xticks(rotation=45, ha='right')
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('genre_distribution.png', dpi=150, bbox_inches='tight')
    print("✅ Saved genre distribution to 'genre_distribution.png'")
    
    print(f"📊 Genre Statistics:")
    print(f"   Total genres: {len(genres)}")
    print(f"   Total songs: {sum(counts)}")
    print(f"   Most common: {max(genre_counts, key=genre_counts.get)} ({max(genre_counts.values())} songs)")

def visualize_timeline():
    """Visualize song publication timeline."""
    print("📅 Visualizing Song Timeline...")
    
    songs = load_dataset()
    
    # Extract years
    years = []
    for song in songs:
        pub_date = song.get('publication_date', '')
        if pub_date and len(pub_date) >= 4:
            try:
                year = int(pub_date[:4])
                years.append(year)
            except ValueError:
                continue
    
    if not years:
        print("❌ No valid year data found")
        return
    
    # Create visualization
    plt.figure(figsize=(12, 6))
    
    plt.hist(years, bins=range(min(years), max(years) + 2), alpha=0.7, edgecolor='black')
    plt.title('Song Publication Timeline')
    plt.xlabel('Year')
    plt.ylabel('Number of Songs')
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('song_timeline.png', dpi=150, bbox_inches='tight')
    print("✅ Saved timeline to 'song_timeline.png'")
    
    print(f"📊 Timeline Statistics:")
    print(f"   Songs with dates: {len(years)}")
    print(f"   Year range: {min(years)} - {max(years)}")
    print(f"   Average year: {np.mean(years):.1f}")

def create_system_report():
    """Create a text report of system statistics."""
    print("📋 Creating System Report...")
    
    songs = load_dataset()
    
    report = []
    report.append("MUSIC AKENATOR SYSTEM REPORT")
    report.append("=" * 40)
    report.append("")
    
    # Basic statistics
    report.append("📊 BASIC STATISTICS")
    report.append(f"Total songs: {len(songs)}")
    report.append("")
    
    # Genre analysis
    all_genres = set()
    genre_counts = {}
    for song in songs:
        genres = song.get('genres', [])
        for genre in genres:
            all_genres.add(genre)
            genre_counts[genre] = genre_counts.get(genre, 0) + 1
    
    report.append("🎵 GENRE ANALYSIS")
    report.append(f"Total genres: {len(all_genres)}")
    report.append("Top 5 genres:")
    for genre, count in sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
        report.append(f"  {genre}: {count} songs")
    report.append("")
    
    # Artist analysis
    all_artists = set()
    solo_artists = 0
    for song in songs:
        artists = song.get('artists', [])
        all_artists.update(artists)
        if len(artists) == 1:
            solo_artists += 1
    
    report.append("🎤 ARTIST ANALYSIS")
    report.append(f"Total artists: {len(all_artists)}")
    report.append(f"Solo songs: {solo_artists}")
    report.append(f"Collaborations: {len(songs) - solo_artists}")
    report.append("")
    
    # Attribute analysis
    report.append("📋 ATTRIBUTE COVERAGE")
    attributes = ['artist_genders', 'artist_types', 'song_types', 'themes', 'instruments']
    for attr in attributes:
        count = sum(1 for song in songs if song.get(attr))
        report.append(f"{attr}: {count}/{len(songs)} songs ({count/len(songs)*100:.1f}%)")
    report.append("")
    
    # Save report
    report_text = '\n'.join(report)
    with open('system_report.txt', 'w') as f:
        f.write(report_text)
    
    print("✅ Saved system report to 'system_report.txt'")
    print(report_text)

def main():
    """Run all visualizations."""
    print("🎨 Music Akenator Visualization Tool")
    print("=" * 50)
    
    try:
        # Check if matplotlib is available
        import matplotlib.pyplot as plt
        print("✅ Matplotlib available for visualizations")
    except ImportError:
        print("❌ Matplotlib not available. Install with: pip install matplotlib")
        return
    
    # Create visualizations
    visualize_song_clusters()
    print()
    
    visualize_genre_distribution()
    print()
    
    visualize_timeline()
    print()
    
    create_system_report()
    print()
    
    print("🎉 All visualizations completed!")
    print("Files created:")
    print("  - song_clusters.png")
    print("  - genre_distribution.png") 
    print("  - song_timeline.png")
    print("  - system_report.txt")

if __name__ == "__main__":
    main()
