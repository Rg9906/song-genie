"""
Neural Embedding System for Song Similarity
Uses metric learning to learn semantic relationships between songs
"""

import json
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from typing import List, Dict, Any, Tuple, Optional
import os
from collections import defaultdict

from backend.logic.config import REQUEST_TIMEOUT_SECONDS


class SongDataset(Dataset):
    """Dataset for training song embeddings"""
    
    def __init__(self, songs: List[Dict[str, Any]], metadata_encoder):
        self.songs = songs
        self.metadata_encoder = metadata_encoder
        self.pairs = self._create_training_pairs()
    
    def _create_training_pairs(self) -> List[Tuple[int, int, float]]:
        """Create (song1_idx, song2_idx, similarity_score) pairs"""
        pairs = []
        
        # Positive pairs (similar songs)
        genre_groups = defaultdict(list)
        era_groups = defaultdict(list)
        artist_groups = defaultdict(list)
        
        for i, song in enumerate(self.songs):
            # Group by genres
            for genre in song.get("genres", []):
                genre_groups[genre].append(i)
            
            # Group by era
            era = self._get_era(song)
            if era:
                era_groups[era].append(i)
            
            # Group by artists (for collaborations)
            for artist in song.get("artists", []):
                artist_groups[artist].append(i)
        
        # Create positive pairs
        for group in [genre_groups, era_groups, artist_groups]:
            for songs_in_group in group.values():
                if len(songs_in_group) >= 2:
                    for i in range(len(songs_in_group)):
                        for j in range(i + 1, len(songs_in_group)):
                            pairs.append((songs_in_group[i], songs_in_group[j], 1.0))
        
        # Create negative pairs (dissimilar songs)
        for i in range(len(self.songs)):
            for j in range(len(self.songs)):
                if i != j and (i, j, 1.0) not in pairs and (j, i, 1.0) not in pairs:
                    # Sample some negative pairs
                    if np.random.random() < 0.1:  # 10% sampling rate
                        pairs.append((i, j, 0.0))
        
        return pairs
    
    def _get_era(self, song: Dict[str, Any]) -> Optional[str]:
        """Extract era from song"""
        pub_date = song.get("publication_date")
        if pub_date and isinstance(pub_date, str) and len(pub_date) >= 4:
            try:
                year = int(pub_date[:4])
                if year < 1990:
                    return "classic"
                elif year < 2000:
                    return "90s"
                elif year < 2010:
                    return "2000s"
                else:
                    return "2010s"
            except ValueError:
                pass
        return None
    
    def __len__(self):
        return len(self.pairs)
    
    def __getitem__(self, idx):
        song1_idx, song2_idx, similarity = self.pairs[idx]
        
        song1_features = self.metadata_encoder.encode(self.songs[song1_idx])
        song2_features = self.metadata_encoder.encode(self.songs[song2_idx])
        
        return (
            torch.FloatTensor(song1_features),
            torch.FloatTensor(song2_features),
            torch.FloatTensor([similarity])
        )


class MetadataEncoder:
    """Encodes song metadata into feature vectors"""
    
    def __init__(self, songs: List[Dict[str, Any]]):
        self.vocabs = self._build_vocabs(songs)
        self.feature_dim = self._calculate_feature_dim()
    
    def _build_vocabs(self, songs: List[Dict[str, Any]]) -> Dict[str, Dict[str, int]]:
        """Build vocabularies for categorical features"""
        vocabs = {}
        
        # Genre vocabulary
        genres = set()
        for song in songs:
            genres.update(song.get("genres", []))
        vocabs["genres"] = {genre: i for i, genre in enumerate(sorted(genres))}
        
        # Artist vocabulary (top artists only)
        artist_counts = defaultdict(int)
        for song in songs:
            for artist in song.get("artists", []):
                artist_counts[artist] += 1
        
        # Top 100 artists
        top_artists = sorted(artist_counts.items(), key=lambda x: x[1], reverse=True)[:100]
        vocabs["artists"] = {artist: i for i, (artist, _) in enumerate(top_artists)}
        vocabs["artists"]["<unknown>"] = len(vocabs["artists"])
        
        # Country vocabulary
        countries = set()
        for song in songs:
            country = song.get("country")
            if country:
                countries.add(country)
        vocabs["countries"] = {country: i for i, country in enumerate(sorted(countries))}
        
        # Language vocabulary
        languages = set()
        for song in songs:
            language = song.get("language")
            if language:
                languages.add(language)
        vocabs["languages"] = {language: i for i, language in enumerate(sorted(languages))}
        
        return vocabs
    
    def _calculate_feature_dim(self) -> int:
        """Calculate total feature dimension"""
        dim = 0
        
        # One-hot encoded genres
        dim += len(self.vocabs["genres"])
        
        # One-hot encoded artists (top 100 + unknown)
        dim += len(self.vocabs["artists"])
        
        # One-hot encoded countries
        dim += len(self.vocabs["countries"])
        
        # One-hot encoded languages
        dim += len(self.vocabs["languages"])
        
        # Numerical features
        dim += 5  # year, decade, duration, bpm, billion_views
        
        # Binary features
        dim += 3  # has_awards, is_soundtrack, is_collaboration
        
        return dim
    
    def encode(self, song: Dict[str, Any]) -> np.ndarray:
        """Encode a single song into a feature vector"""
        features = np.zeros(self.feature_dim)
        idx = 0
        
        # Genre one-hot encoding
        for genre in song.get("genres", []):
            if genre in self.vocabs["genres"]:
                features[idx + self.vocabs["genres"][genre]] = 1.0
        idx += len(self.vocabs["genres"])
        
        # Artist one-hot encoding
        for artist in song.get("artists", []):
            if artist in self.vocabs["artists"]:
                features[idx + self.vocabs["artists"][artist]] = 1.0
                break  # Use first known artist
        if not any(artist in self.vocabs["artists"] for artist in song.get("artists", [])):
            features[idx + self.vocabs["artists"]["<unknown>"]] = 1.0
        idx += len(self.vocabs["artists"])
        
        # Country one-hot encoding
        country = song.get("country")
        if country and country in self.vocabs["countries"]:
            features[idx + self.vocabs["countries"][country]] = 1.0
        idx += len(self.vocabs["countries"])
        
        # Language one-hot encoding
        language = song.get("language")
        if language and language in self.vocabs["languages"]:
            features[idx + self.vocabs["languages"][language]] = 1.0
        idx += len(self.vocabs["languages"])
        
        # Numerical features (normalized)
        pub_date = song.get("publication_date")
        if pub_date and isinstance(pub_date, str) and len(pub_date) >= 4:
            try:
                year = int(pub_date[:4])
                features[idx] = (year - 1950) / 80  # Normalize to 0-1 range (1950-2030)
            except ValueError:
                pass
        idx += 1
        
        # Duration (normalized)
        duration = song.get("duration")
        if duration:
            features[idx] = min(duration / 300, 1.0)  # Normalize to 0-1 (up to 5 minutes)
        idx += 1
        
        # BPM (normalized)
        bpm = song.get("bpm")
        if bpm:
            features[idx] = (bpm - 60) / 120  # Normalize to 0-1 (60-180 BPM)
        idx += 1
        
        # Billion views (binary)
        features[idx] = 1.0 if song.get("billion_views") else 0.0
        idx += 1
        
        # Has awards (binary)
        features[idx] = 1.0 if song.get("awards") else 0.0
        idx += 1
        
        # Is soundtrack (binary)
        features[idx] = 1.0 if song.get("films") or song.get("tv_series") else 0.0
        idx += 1
        
        # Is collaboration (binary)
        features[idx] = 1.0 if len(song.get("artists", [])) > 1 else 0.0
        
        return features


class SongEmbeddingNet(nn.Module):
    """Neural network for learning song embeddings"""
    
    def __init__(self, input_dim: int, embedding_dim: int = 128):
        super(SongEmbeddingNet, self).__init__()
        
        self.embedding_dim = embedding_dim
        
        # Shared encoder network
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 256),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(128, embedding_dim),
            nn.Tanh()  # Normalize embeddings to [-1, 1]
        )
    
    def forward(self, x):
        return self.encoder(x)
    
    def get_embedding(self, song_features):
        """Get embedding for a single song"""
        return self.encoder(song_features)


class ContrastiveLoss(nn.Module):
    """Contrastive loss for metric learning"""
    
    def __init__(self, margin: float = 1.0):
        super(ContrastiveLoss, self).__init__()
        self.margin = margin
    
    def forward(self, embedding1, embedding2, similarity):
        # Calculate cosine similarity
        cos_sim = nn.functional.cosine_similarity(embedding1, embedding2, dim=1)
        
        # Convert similarity (0 or 1) to target values
        target = similarity.squeeze()
        
        # Contrastive loss
        loss = (1 - target) * 0.5 * (cos_sim ** 2) + \
               target * 0.5 * torch.clamp(self.margin - cos_sim, min=0) ** 2
        
        return loss.mean()


class EmbeddingTrainer:
    """Trainer for song embeddings"""
    
    def __init__(self, songs: List[Dict[str, Any]], embedding_dim: int = 128):
        self.songs = songs
        self.embedding_dim = embedding_dim
        self.metadata_encoder = MetadataEncoder(songs)
        self.model = SongEmbeddingNet(self.metadata_encoder.feature_dim, embedding_dim)
        self.criterion = ContrastiveLoss(margin=1.0)
        self.optimizer = optim.Adam(self.model.parameters(), lr=0.001)
        
        # Store embeddings for songs
        self.song_embeddings = {}
    
    def train(self, epochs: int = 100, batch_size: int = 32):
        """Train the embedding model"""
        dataset = SongDataset(self.songs, self.metadata_encoder)
        dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)
        
        self.model.train()
        
        for epoch in range(epochs):
            total_loss = 0.0
            
            for batch_idx, (song1_features, song2_features, similarity) in enumerate(dataloader):
                self.optimizer.zero_grad()
                
                # Get embeddings
                embedding1 = self.model(song1_features)
                embedding2 = self.model(song2_features)
                
                # Calculate loss
                loss = self.criterion(embedding1, embedding2, similarity)
                
                # Backward pass
                loss.backward()
                self.optimizer.step()
                
                total_loss += loss.item()
            
            if epoch % 20 == 0:
                print(f"Epoch {epoch}, Loss: {total_loss / len(dataloader):.4f}")
    
    def compute_embeddings(self):
        """Compute and store embeddings for all songs"""
        self.model.eval()
        
        with torch.no_grad():
            for i, song in enumerate(self.songs):
                features = self.metadata_encoder.encode(song)
                features_tensor = torch.FloatTensor(features).unsqueeze(0)
                embedding = self.model.get_embedding(features_tensor)
                self.song_embeddings[song["title"]] = embedding.squeeze().numpy()
    
    def find_similar_songs(self, song_title: str, top_k: int = 10) -> List[Tuple[str, float]]:
        """Find most similar songs to a given song"""
        if song_title not in self.song_embeddings:
            return []
        
        target_embedding = self.song_embeddings[song_title]
        similarities = []
        
        for title, embedding in self.song_embeddings.items():
            if title != song_title:
                # Calculate cosine similarity
                similarity = np.dot(target_embedding, embedding) / (
                    np.linalg.norm(target_embedding) * np.linalg.norm(embedding)
                )
                similarities.append((title, similarity))
        
        # Sort by similarity and return top-k
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]
    
    def save_model(self, filepath: str):
        """Save the trained model and embeddings"""
        torch.save({
            'model_state_dict': self.model.state_dict(),
            'metadata_encoder': self.metadata_encoder,
            'song_embeddings': self.song_embeddings,
            'embedding_dim': self.embedding_dim
        }, filepath)
    
    def load_model(self, filepath: str):
        """Load a trained model and embeddings"""
        checkpoint = torch.load(filepath, map_location='cpu')
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.metadata_encoder = checkpoint['metadata_encoder']
        self.song_embeddings = checkpoint['song_embeddings']
        self.embedding_dim = checkpoint['embedding_dim']


def train_embeddings(songs: List[Dict[str, Any]], epochs: int = 100) -> EmbeddingTrainer:
    """Train song embeddings from song data"""
    print("🧠 Training neural song embeddings...")
    
    trainer = EmbeddingTrainer(songs, embedding_dim=128)
    trainer.train(epochs=epochs)
    trainer.compute_embeddings()
    
    print(f"✅ Trained embeddings for {len(trainer.song_embeddings)} songs")
    return trainer
