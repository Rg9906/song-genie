"""
Enhanced Neural Embedding System
Improved training pipeline with proper validation and efficient similarity search
"""

import json
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
import logging
import pickle
import os

# Try to import PyTorch, but make it optional
try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    from torch.utils.data import Dataset, DataLoader
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("PyTorch not available - embedding training disabled")

# Try to import FAISS for efficient similarity search
try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("FAISS not available - using numpy for similarity search")

# Try to import sklearn
try:
    from sklearn.preprocessing import LabelEncoder
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score
    from sklearn.decomposition import PCA
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("sklearn not available - using basic fallbacks")

logger = logging.getLogger(__name__)

# Only define PyTorch classes if available
if TORCH_AVAILABLE:
    class SongDataset(Dataset):
        """PyTorch dataset for song embeddings"""
        
        def __init__(self, songs: List[Dict[str, Any]], label_encoders: Dict[str, Any]):
            self.songs = songs
            self.label_encoders = label_encoders
            self.features = self._extract_features()
            self.positive_pairs, self.negative_pairs = self._create_pairs()
        
        def _extract_features(self) -> Any:
            """Extract and normalize features from songs"""
            features = []
            
            for song in self.songs:
                song_features = []
                
                # Categorical features
                categorical_features = ['genres', 'artists', 'country', 'decade', 'era']
                for feature in categorical_features:
                    values = song.get(feature, [])
                    if isinstance(values, list) and values:
                        # Use first value for simplicity
                        encoded = self.label_encoders.get(feature, {}).get(values[0], 0)
                        song_features.append(encoded)
                    else:
                        song_features.append(0)  # Unknown category
                
                # Numerical features
                numerical_features = ['release_year', 'duration', 'bpm']
                for feature in numerical_features:
                    value = song.get(feature, 0)
                    if isinstance(value, str):
                        value = 0
                    song_features.append(float(value))
                
                # Boolean features
                boolean_features = ['is_collaboration', 'is_soundtrack', 'is_viral_hit']
                for feature in boolean_features:
                    value = song.get(feature, False)
                    song_features.append(1.0 if value else 0.0)
                
                features.append(song_features)
            
            return torch.tensor(features, dtype=torch.float32)
        
        def _create_pairs(self) -> Tuple[List[Tuple[int, int]], List[Tuple[int, int]]]:
            """Create positive and negative pairs for contrastive learning"""
            positive_pairs = []
            negative_pairs = []
            
            # Create positive pairs (songs with same genre)
            genre_to_songs = {}
            for i, song in enumerate(self.songs):
                genres = song.get('genres', [])
                if genres:
                    genre = genres[0]  # Use primary genre
                    if genre not in genre_to_songs:
                        genre_to_songs[genre] = []
                    genre_to_songs[genre].append(i)
            
            for genre, song_indices in genre_to_songs.items():
                if len(song_indices) >= 2:
                    for i in range(len(song_indices)):
                        for j in range(i + 1, min(i + 3, len(song_indices))):
                            positive_pairs.append((song_indices[i], song_indices[j]))
            
            # Create negative pairs (songs with different genres)
            all_indices = list(range(len(self.songs)))
            for i in range(len(self.songs)):
                for _ in range(2):  # 2 negative pairs per song
                    j = np.random.choice(all_indices)
                    if i != j and self._are_different_genres(i, j):
                        negative_pairs.append((i, j))
            
            return positive_pairs, negative_pairs
        
        def _are_different_genres(self, i: int, j: int) -> bool:
            """Check if two songs have different genres"""
            genres_i = set(self.songs[i].get('genres', []))
            genres_j = set(self.songs[j].get('genres', []))
            return len(genres_i.intersection(genres_j)) == 0
        
        def __len__(self):
            return len(self.positive_pairs) + len(self.negative_pairs)
        
        def __getitem__(self, idx):
            if idx < len(self.positive_pairs):
                i, j = self.positive_pairs[idx]
                label = 1.0
            else:
                i, j = self.negative_pairs[idx - len(self.positive_pairs)]
                label = 0.0
            
            return (
                self.features[i],
                self.features[j],
                torch.tensor([label], dtype=torch.float32)
            )

    class EnhancedEmbeddingModel(nn.Module):
        """Enhanced neural embedding model with better architecture"""
        
        def __init__(self, input_dim: int, embedding_dim: int = 128):
            super().__init__()
            
            self.embedding_dim = embedding_dim
            
            # Better architecture with batch normalization
            self.encoder = nn.Sequential(
                nn.Linear(input_dim, 256),
                nn.BatchNorm1d(256),
                nn.ReLU(),
                nn.Dropout(0.3),
                
                nn.Linear(256, 128),
                nn.BatchNorm1d(128),
                nn.ReLU(),
                nn.Dropout(0.3),
                
                nn.Linear(128, embedding_dim),
                nn.BatchNorm1d(embedding_dim),
            )
            
            # Projection head for contrastive learning
            self.projection = nn.Sequential(
                nn.Linear(embedding_dim, 64),
                nn.ReLU(),
                nn.Linear(64, embedding_dim)
            )
        
        def forward(self, x):
            embeddings = self.encoder(x)
            # L2 normalize embeddings
            embeddings = F.normalize(embeddings, p=2, dim=1)
            return embeddings
        
        def get_projections(self, x):
            """Get projections for contrastive learning"""
            embeddings = self.forward(x)
            projections = self.projection(embeddings)
            projections = F.normalize(projections, p=2, dim=1)
            return projections

    class ContrastiveLoss(nn.Module):
        """Enhanced contrastive loss for better training"""
        
        def __init__(self, margin: float = 1.0, temperature: float = 0.1):
            super().__init__()
            self.margin = margin
            self.temperature = temperature
        
        def forward(self, embeddings1, embeddings2, labels):
            # Calculate cosine similarity
            similarity = F.cosine_similarity(embeddings1, embeddings2, dim=1)
            
            # Contrastive loss
            positive_loss = labels * torch.pow(1 - similarity, 2)
            negative_loss = (1 - labels) * torch.pow(
                torch.clamp(similarity - self.margin, min=0.0), 2
            )
            
            loss = positive_loss + negative_loss
            return loss.mean()


class EnhancedEmbeddingTrainer:
    """Enhanced embedding trainer with proper validation and metrics"""
    
    def __init__(self, embedding_dim: int = 128):
        self.embedding_dim = embedding_dim
        self.model = None
        self.label_encoders = {}
        self.embeddings = None
        self.song_metadata = []
        
    def prepare_data(self, songs: List[Dict[str, Any]]) -> Tuple[Any, Any]:
        """Prepare and split data for training"""
        logger.info(f"📊 Preparing {len(songs)} songs for embedding training")
        
        # Create label encoders
        self.label_encoders = self._create_label_encoders(songs)
        
        # Create datasets
        full_dataset = SongDataset(songs, self.label_encoders)
        
        # Split into train/validation (80/20)
        train_size = int(0.8 * len(songs))
        val_size = len(songs) - train_size
        
        train_indices = list(range(train_size))
        val_indices = list(range(train_size, len(songs)))
        
        train_dataset = torch.utils.data.Subset(full_dataset, train_indices)
        val_dataset = torch.utils.data.Subset(full_dataset, val_indices)
        
        logger.info(f"📊 Train: {len(train_dataset)}, Validation: {len(val_dataset)}")
        return train_dataset, val_dataset
    
    def _create_label_encoders(self, songs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create label encoders for categorical features"""
        encoders = {}
        
        # Collect all values for each categorical feature
        categorical_features = ['genres', 'artists', 'country', 'decade', 'era']
        
        for feature in categorical_features:
            all_values = []
            for song in songs:
                values = song.get(feature, [])
                if isinstance(values, list) and values:
                    all_values.append(values[0])  # Use first value
            
            if SKLEARN_AVAILABLE:
                encoders[feature] = LabelEncoder()
                encoders[feature].fit(all_values)
            else:
                # Simple mapping fallback
                encoders[feature] = {val: i for i, val in enumerate(all_values)}
        
        return encoders
    
    def train_embeddings(self, songs: List[Dict[str, Any]], 
                      epochs: int = 100, batch_size: int = 32) -> Dict[str, Any]:
        """Train embeddings with proper validation"""
        logger.info("🧠 Training enhanced neural embeddings...")
        
        # Prepare data
        train_dataset, val_dataset = self.prepare_data(songs)
        
        # Create data loaders
        train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
        val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)
        
        # Initialize model
        input_dim = self._get_input_dim(songs[0] if songs else {})
        self.model = EnhancedEmbeddingModel(input_dim, self.embedding_dim)
        
        # Training setup
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model.to(device)
        
        criterion = ContrastiveLoss(margin=1.0)
        optimizer = torch.optim.Adam(self.model.parameters(), lr=0.001, weight_decay=1e-5)
        scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=10)
        
        # Training metrics
        train_losses = []
        val_losses = []
        best_val_loss = float('inf')
        
        for epoch in range(epochs):
            # Training phase
            self.model.train()
            train_loss = 0.0
            
            for batch_idx, (emb1, emb2, labels) in enumerate(train_loader):
                emb1, emb2, labels = emb1.to(device), emb2.to(device), labels.to(device)
                
                optimizer.zero_grad()
                embeddings1 = self.model(emb1)
                embeddings2 = self.model(emb2)
                
                loss = criterion(embeddings1, embeddings2, labels.squeeze())
                loss.backward()
                optimizer.step()
                
                train_loss += loss.item()
            
            avg_train_loss = train_loss / len(train_loader)
            train_losses.append(avg_train_loss)
            
            # Validation phase
            val_loss = self._validate_model(val_loader, device, criterion)
            val_losses.append(val_loss)
            
            scheduler.step(val_loss)
            
            # Save best model
            if val_loss < best_val_loss:
                best_val_loss = val_loss
                self._save_checkpoint(epoch, val_loss)
            
            # Log progress
            if epoch % 10 == 0:
                logger.info(f"Epoch {epoch}: Train Loss = {avg_train_loss:.4f}, Val Loss = {val_loss:.4f}")
        
        # Generate final embeddings
        self._generate_final_embeddings(songs, device)
        
        # Build efficient similarity search index
        self._build_similarity_index()
        
        return {
            'train_losses': train_losses,
            'val_losses': val_losses,
            'best_val_loss': best_val_loss,
            'embedding_dim': self.embedding_dim,
            'num_songs': len(songs)
        }
    
    def _validate_model(self, val_loader: DataLoader, device: torch.device, criterion: nn.Module) -> float:
        """Validate model performance"""
        self.model.eval()
        val_loss = 0.0
        
        with torch.no_grad():
            for emb1, emb2, labels in val_loader:
                emb1, emb2, labels = emb1.to(device), emb2.to(device), labels.to(device)
                
                embeddings1 = self.model(emb1)
                embeddings2 = self.model(emb2)
                
                loss = criterion(embeddings1, embeddings2, labels.squeeze())
                val_loss += loss.item()
        
        return val_loss / len(val_loader)
    
    def _generate_final_embeddings(self, songs: List[Dict[str, Any]], device: torch.device):
        """Generate final embeddings for all songs"""
        logger.info("🎯 Generating final embeddings...")
        
        self.model.eval()
        self.embeddings = []
        self.song_metadata = songs
        
        with torch.no_grad():
            for song in songs:
                features = self._extract_single_features(song)
                features_tensor = torch.tensor(features, dtype=torch.float32).unsqueeze(0).to(device)
                
                embedding = self.model(features_tensor)
                self.embeddings.append(embedding.cpu().numpy().flatten())
        
        self.embeddings = np.array(self.embeddings)
        logger.info(f"✅ Generated {len(self.embeddings)} embeddings of shape {self.embeddings.shape}")
    
    def _extract_single_features(self, song: Dict[str, Any]) -> List[float]:
        """Extract features for a single song"""
        features = []
        
        # Categorical features
        categorical_features = ['genres', 'artists', 'country', 'decade', 'era']
        for feature in categorical_features:
            values = song.get(feature, [])
            if isinstance(values, list) and values:
                encoded = self.label_encoders.get(feature, LabelEncoder()).fit_transform([values[0]])[0]
                features.append(encoded)
            else:
                features.append(0)
        
        # Numerical features
        numerical_features = ['release_year', 'duration', 'bpm']
        for feature in numerical_features:
            value = song.get(feature, 0)
            if isinstance(value, str):
                value = 0
            features.append(float(value))
        
        # Boolean features
        boolean_features = ['is_collaboration', 'is_soundtrack', 'is_viral_hit']
        for feature in boolean_features:
            value = song.get(feature, False)
            features.append(1.0 if value else 0.0)
        
        return features
    
    def _build_similarity_index(self):
        """Build FAISS index for efficient similarity search"""
        logger.info("🔍 Building similarity search index...")
        
        # Normalize embeddings
        normalized_embeddings = self.embeddings / np.linalg.norm(self.embeddings, axis=1, keepdims=True)
        
        # Build FAISS index
        self.similarity_index = faiss.IndexFlatIP(self.embedding_dim)  # Inner product for cosine similarity
        self.similarity_index.add(normalized_embeddings.astype(np.float32))
        
        logger.info(f"✅ Built index with {self.similarity_index.ntotal} embeddings")
    
    def find_similar_songs(self, query_song: Dict[str, Any], top_k: int = 5) -> List[Tuple[int, float]]:
        """Find similar songs using efficient similarity search"""
        if self.embeddings is None or self.similarity_index is None:
            return []
        
        # Extract and encode query features
        query_features = self._extract_single_features(query_song)
        query_embedding = self._generate_query_embedding(query_features)
        
        # Search in index
        scores, indices = self.similarity_index.search(
            query_embedding.astype(np.float32), top_k
        )
        
        # Return results with scores
        results = []
        for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
            results.append((int(idx), float(score)))
        
        return results
    
    def _generate_query_embedding(self, features: List[float]) -> np.ndarray:
        """Generate embedding for query song"""
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        self.model.eval()
        with torch.no_grad():
            features_tensor = torch.tensor(features, dtype=torch.float32).unsqueeze(0).to(device)
            embedding = self.model(features_tensor)
            return embedding.cpu().numpy().flatten()
    
    def _get_input_dim(self, sample_song: Dict[str, Any]) -> int:
        """Get input dimension from sample song"""
        categorical_features = ['genres', 'artists', 'country', 'decade', 'era']
        numerical_features = ['release_year', 'duration', 'bpm']
        boolean_features = ['is_collaboration', 'is_soundtrack', 'is_viral_hit']
        
        return len(categorical_features + numerical_features + boolean_features)
    
    def _save_checkpoint(self, epoch: int, val_loss: float):
        """Save model checkpoint"""
        checkpoint = {
            'epoch': epoch,
            'model_state_dict': self.model.state_dict(),
            'val_loss': val_loss,
            'label_encoders': self.label_encoders,
            'embedding_dim': self.embedding_dim
        }
        
        os.makedirs('checkpoints', exist_ok=True)
        torch.save(checkpoint, f'checkpoints/embedding_model_epoch_{epoch}.pth')
    
    def save_embeddings(self, filepath: str):
        """Save embeddings and metadata"""
        data = {
            'embeddings': self.embeddings.tolist(),
            'song_metadata': self.song_metadata,
            'label_encoders': {k: v.classes_.tolist() for k, v in self.label_encoders.items()},
            'embedding_dim': self.embedding_dim
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"💾 Saved embeddings to {filepath}")
    
    def load_embeddings(self, filepath: str):
        """Load pre-trained embeddings"""
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        self.embeddings = np.array(data['embeddings'])
        self.song_metadata = data['song_metadata']
        self.embedding_dim = data['embedding_dim']
        
        # Rebuild label encoders
        self.label_encoders = {}
        for feature, classes in data['label_encoders'].items():
            encoder = LabelEncoder()
            encoder.classes_ = np.array(classes)
            self.label_encoders[feature] = encoder
        
        # Rebuild similarity index
        self._build_similarity_index()
        
        logger.info(f"📥 Loaded {len(self.embeddings)} embeddings from {filepath}")


class FallbackEmbeddingTrainer:
    """Fallback embedding trainer using sklearn when PyTorch is not available"""
    
    def __init__(self, embedding_dim: int = 128):
        self.embedding_dim = embedding_dim
        self.embeddings = None
        self.song_metadata = []
        self.label_encoders = {}
        
    def train_embeddings(self, songs: List[Dict[str, Any]], 
                      epochs: int = 100, batch_size: int = 32) -> Dict[str, Any]:
        """Train simple embeddings using basic methods"""
        logger.info("🧠 Training fallback embeddings using basic methods...")
        
        # Create feature matrix
        features = self._extract_features_matrix(songs)
        
        if SKLEARN_AVAILABLE:
            # Use PCA for dimensionality reduction
            pca = PCA(n_components=min(self.embedding_dim, features.shape[1]), random_state=42)
            self.embeddings = pca.fit_transform(features)
            self.pca = pca
            method = 'pca_fallback'
        else:
            # Use simple SVD from numpy
            logger.info("Using numpy SVD for dimensionality reduction")
            
            # Center the data
            features_centered = features - np.mean(features, axis=0)
            
            # Compute SVD
            if min(features_centered.shape) < self.embedding_dim:
                # Use all available components
                n_components = min(features_centered.shape)
            else:
                n_components = self.embedding_dim
            
            U, S, Vt = np.linalg.svd(features_centered, full_matrices=False)
            
            # Take top components
            self.embeddings = U[:, :n_components] * S[:n_components]
            method = 'svd_fallback'
        
        # Store metadata
        self.song_metadata = songs
        
        # Create label encoders
        self.label_encoders = self._create_label_encoders(songs)
        
        # Build simple similarity search
        self._build_similarity_index()
        
        logger.info(f"✅ Fallback embeddings trained: {self.embeddings.shape}")
        
        return {
            'train_losses': [0.0],  # No training loss for PCA/SVD
            'val_losses': [0.0],
            'best_val_loss': 0.0,
            'embedding_dim': self.embedding_dim,
            'num_songs': len(songs),
            'method': method
        }
    
    def _extract_features_matrix(self, songs: List[Dict[str, Any]]) -> np.ndarray:
        """Extract feature matrix from songs"""
        features = []
        
        for song in songs:
            song_features = []
            
            # Categorical features (one-hot encoded)
            categorical_features = ['genres', 'artists', 'country', 'decade', 'era']
            for feature in categorical_features:
                values = song.get(feature, [])
                if isinstance(values, list) and values:
                    song_features.append(hash(values[0]) % 1000)  # Simple encoding
                else:
                    song_features.append(0)
            
            # Numerical features
            numerical_features = ['release_year', 'duration', 'bpm']
            for feature in numerical_features:
                value = song.get(feature, 0)
                if isinstance(value, str):
                    value = 0
                song_features.append(float(value))
            
            # Boolean features
            boolean_features = ['is_collaboration', 'is_soundtrack', 'is_viral_hit']
            for feature in boolean_features:
                value = song.get(feature, False)
                song_features.append(1.0 if value else 0.0)
            
            features.append(song_features)
        
        return np.array(features, dtype=np.float32)
    
    def _create_label_encoders(self, songs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create simple label encoders"""
        encoders = {}
        
        categorical_features = ['genres', 'artists', 'country', 'decade', 'era']
        for feature in categorical_features:
            all_values = set()
            for song in songs:
                values = song.get(feature, [])
                if isinstance(values, list) and values:
                    all_values.add(values[0])
            
            encoders[feature] = list(all_values)
        
        return encoders
    
    def _build_similarity_index(self):
        """Build simple similarity search using numpy"""
        if self.embeddings is not None:
            # Normalize embeddings for cosine similarity
            norms = np.linalg.norm(self.embeddings, axis=1, keepdims=True)
            self.normalized_embeddings = self.embeddings / (norms + 1e-8)
    
    def find_similar_songs(self, query_song: Dict[str, Any], top_k: int = 5) -> List[Tuple[int, float]]:
        """Find similar songs using numpy"""
        if self.embeddings is None:
            return []
        
        # Extract query features
        query_features = self._extract_single_features(query_song)
        
        # Use PCA transform if available
        if hasattr(self, 'pca'):
            query_embedding = self.pca.transform([query_features])
        else:
            # Simple projection
            if len(query_features) > self.embedding_dim:
                query_embedding = np.array([query_features[:self.embedding_dim]])
            else:
                # Pad with zeros
                padded = query_features + [0.0] * (self.embedding_dim - len(query_features))
                query_embedding = np.array([padded])
        
        # Calculate similarities
        similarities = np.dot(self.normalized_embeddings, query_embedding[0])
        
        # Get top-k indices
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        
        return [(int(idx), float(similarities[idx])) for idx in top_indices]
    
    def _extract_single_features(self, song: Dict[str, Any]) -> List[float]:
        """Extract features for a single song"""
        features = []
        
        # Categorical features
        categorical_features = ['genres', 'artists', 'country', 'decade', 'era']
        for feature in categorical_features:
            values = song.get(feature, [])
            if isinstance(values, list) and values:
                features.append(hash(values[0]) % 1000)
            else:
                features.append(0)
        
        # Numerical features
        numerical_features = ['release_year', 'duration', 'bpm']
        for feature in numerical_features:
            value = song.get(feature, 0)
            if isinstance(value, str):
                value = 0
            features.append(float(value))
        
        # Boolean features
        boolean_features = ['is_collaboration', 'is_soundtrack', 'is_viral_hit']
        for feature in boolean_features:
            value = song.get(feature, False)
            features.append(1.0 if value else 0.0)
        
        return features
    
    def save_embeddings(self, filepath: str):
        """Save embeddings and metadata"""
        data = {
            'embeddings': self.embeddings.tolist() if self.embeddings is not None else [],
            'song_metadata': self.song_metadata,
            'label_encoders': self.label_encoders,
            'embedding_dim': self.embedding_dim,
            'method': 'pca_fallback'
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"💾 Saved fallback embeddings to {filepath}")


def create_enhanced_trainer(embedding_dim: int = 128):
    """Factory function to create enhanced embedding trainer with fallback"""
    if TORCH_AVAILABLE:
        return EnhancedEmbeddingTrainer(embedding_dim)
    else:
        logger.warning("Using fallback embedding trainer (PyTorch not available)")
        return FallbackEmbeddingTrainer(embedding_dim)
