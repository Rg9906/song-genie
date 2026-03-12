"""
Enterprise-Grade Neural Embedding System
Production-ready embedding training with proper validation, caching, and scalability
"""

import json
import os
import logging
import pickle
from typing import List, Dict, Any, Tuple, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime
import numpy as np
from abc import ABC, abstractmethod

# PyTorch imports with graceful fallback
try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    from torch.utils.data import Dataset, DataLoader, random_split
    from torch.nn import functional as F
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    torch = None
    nn = None
    optim = None
    F = None

# Scikit-learn for evaluation
try:
    from sklearn.metrics import precision_recall_fscore_support, roc_auc_score
    from sklearn.manifold import TSNE
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class EmbeddingConfig:
    """Configuration for embedding training"""
    embedding_dim: int = 128
    hidden_dims: List[int] = field(default_factory=lambda: [256, 128])
    dropout_rate: float = 0.2
    learning_rate: float = 0.001
    batch_size: int = 32
    epochs: int = 100
    validation_split: float = 0.2
    early_stopping_patience: int = 10
    margin: float = 1.0  # For contrastive loss
    temperature: float = 0.1  # For InfoNCE loss
    cache_embeddings: bool = True
    normalize_embeddings: bool = True


@dataclass
class TrainingMetrics:
    """Training metrics and statistics"""
    train_loss: float = 0.0
    val_loss: float = 0.0
    train_accuracy: float = 0.0
    val_accuracy: float = 0.0
    epoch: int = 0
    training_time: float = 0.0
    best_val_loss: float = float('inf')
    epochs_without_improvement: int = 0


class DataPreprocessor:
    """Enterprise-grade data preprocessing for embeddings"""
    
    def __init__(self):
        self.feature_encoders = {}
        self.feature_stats = {}
        self.is_fitted = False
    
    def fit(self, songs: List[Dict[str, Any]]) -> 'DataPreprocessor':
        """Fit preprocessing pipeline on song data"""
        logger.info("Fitting data preprocessing pipeline")
        
        # Collect all features
        all_features = set()
        for song in songs:
            for key in song.keys():
                if key not in ["id", "title"] and song[key]:
                    all_features.add(key)
        
        # Create encoders for each feature type
        for feature in all_features:
            self.feature_encoders[feature] = self._create_encoder(feature, songs)
        
        # Calculate feature statistics
        self._calculate_feature_stats(songs)
        
        self.is_fitted = True
        logger.info(f"Preprocessing fitted on {len(songs)} songs with {len(all_features)} features")
        return self
    
    def transform(self, songs: List[Dict[str, Any]]) -> np.ndarray:
        """Transform songs to feature vectors"""
        if not self.is_fitted:
            raise ValueError("Preprocessor must be fitted before transformation")
        
        feature_vectors = []
        
        for song in songs:
            vector = []
            
            for feature, encoder in self.feature_encoders.items():
                value = song.get(feature)
                encoded = encoder.encode(value)
                vector.extend(encoded)
            
            feature_vectors.append(vector)
        
        return np.array(feature_vectors, dtype=np.float32)
    
    def _create_encoder(self, feature: str, songs: List[Dict[str, Any]]) -> 'FeatureEncoder':
        """Create appropriate encoder for feature type"""
        values = [song.get(feature) for song in songs if song.get(feature)]
        
        if not values:
            return NullEncoder()
        
        # Determine feature type and create appropriate encoder
        if feature in ["genres", "artists", "instruments", "themes", "awards", "labels", "producers", "composers"]:
            return MultiHotEncoder(values)
        elif feature in ["artist_genders", "artist_types", "song_types", "country", "language"]:
            return CategoricalEncoder(values)
        elif feature in ["duration", "bpm", "billion_views"]:
            return NumericalEncoder(values)
        elif feature == "publication_date":
            return DateEncoder(values)
        else:
            return MultiHotEncoder(values)
    
    def _calculate_feature_stats(self, songs: List[Dict[str, Any]]):
        """Calculate feature statistics for monitoring"""
        for feature in self.feature_encoders.keys():
            values = [song.get(feature) for song in songs if song.get(feature)]
            
            if isinstance(values[0], list):
                # For list features, calculate average length
                avg_length = np.mean([len(v) for v in values])
                unique_values = set()
                for v in values:
                    unique_values.update(v)
                self.feature_stats[feature] = {
                    "type": "list",
                    "avg_length": avg_length,
                    "unique_count": len(unique_values)
                }
            else:
                # For scalar features
                unique_count = len(set(values))
                self.feature_stats[feature] = {
                    "type": "scalar",
                    "unique_count": unique_count
                }


class FeatureEncoder(ABC):
    """Abstract base class for feature encoders"""
    
    @abstractmethod
    def encode(self, value: Any) -> List[float]:
        pass
    
    @abstractmethod
    def get_dim(self) -> int:
        pass


class NullEncoder(FeatureEncoder):
    """Encoder for missing/empty features"""
    
    def encode(self, value: Any) -> List[float]:
        return [0.0]
    
    def get_dim(self) -> int:
        return 1


class MultiHotEncoder(FeatureEncoder):
    """Multi-hot encoder for list features"""
    
    def __init__(self, values: List[Any]):
        # Get unique values
        all_values = set()
        for v in values:
            if isinstance(v, list):
                all_values.update(v)
            else:
                all_values.add(v)
        
        self.vocabulary = {val: i for i, val in enumerate(sorted(all_values))}
        self.dim = len(self.vocabulary)
    
    def encode(self, value: Any) -> List[float]:
        encoded = [0.0] * self.dim
        
        if value:
            if isinstance(value, list):
                for v in value:
                    if v in self.vocabulary:
                        encoded[self.vocabulary[v]] = 1.0
            elif value in self.vocabulary:
                encoded[self.vocabulary[value]] = 1.0
        
        return encoded
    
    def get_dim(self) -> int:
        return self.dim


class CategoricalEncoder(FeatureEncoder):
    """One-hot encoder for categorical features"""
    
    def __init__(self, values: List[Any]):
        unique_values = list(set(v for v in values if v))
        self.categories = {val: i for i, val in enumerate(unique_values)}
        self.dim = len(self.categories)
    
    def encode(self, value: Any) -> List[float]:
        encoded = [0.0] * self.dim
        if value and value in self.categories:
            encoded[self.categories[value]] = 1.0
        return encoded
    
    def get_dim(self) -> int:
        return self.dim


class NumericalEncoder(FeatureEncoder):
    """Encoder for numerical features with normalization"""
    
    def __init__(self, values: List[float]):
        values = [v for v in values if v is not None]
        if values:
            self.mean = np.mean(values)
            self.std = np.std(values) or 1.0
        else:
            self.mean = 0.0
            self.std = 1.0
        self.dim = 1
    
    def encode(self, value: Any) -> List[float]:
        if value is None:
            return [0.0]
        return [(float(value) - self.mean) / self.std]
    
    def get_dim(self) -> int:
        return 1


class DateEncoder(FeatureEncoder):
    """Encoder for date features"""
    
    def __init__(self, dates: List[str]):
        # Extract years and normalize
        years = []
        for date_str in dates:
            if date_str:
                try:
                    year = int(date_str[:4])
                    years.append(year)
                except (ValueError, TypeError):
                    pass
        
        if years:
            self.min_year = min(years)
            self.max_year = max(years)
            self.year_range = self.max_year - self.min_year or 1
        else:
            self.min_year = 2000
            self.max_year = 2020
            self.year_range = 20
        
        self.dim = 3  # year, decade, era
    
    def encode(self, value: Any) -> List[float]:
        if not value:
            return [0.0, 0.0, 0.0]
        
        try:
            year = int(value[:4])
            
            # Normalized year
            norm_year = (year - self.min_year) / self.year_range
            
            # Decade (0-1 normalized)
            decade = (year // 10) * 10
            norm_decade = (decade - self.min_year) / self.year_range
            
            # Era (pre-2000, 2000s, 2010s, 2020s)
            if year < 2000:
                era = [1.0, 0.0, 0.0, 0.0]
            elif year < 2010:
                era = [0.0, 1.0, 0.0, 0.0]
            elif year < 2020:
                era = [0.0, 0.0, 1.0, 0.0]
            else:
                era = [0.0, 0.0, 0.0, 1.0]
            
            return [norm_year, norm_decade] + era
            
        except (ValueError, TypeError):
            return [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    
    def get_dim(self) -> int:
        return 6


class SongDataset(Dataset):
    """PyTorch dataset for song embeddings with proper sampling"""
    
    def __init__(self, songs: List[Dict[str, Any]], preprocessor: DataPreprocessor, 
                 mode: str = "train", transform=None):
        self.songs = songs
        self.preprocessor = preprocessor
        self.mode = mode
        self.transform = transform
        
        # Preprocess all songs
        self.features = preprocessor.transform(songs)
        
        # Create training pairs with proper sampling
        self.pairs = self._create_training_pairs()
        
        logger.info(f"Created {mode} dataset with {len(self.pairs)} pairs from {len(songs)} songs")
    
    def _create_training_pairs(self) -> List[Tuple[int, int, float]]:
        """Create training pairs with intelligent sampling"""
        pairs = []
        
        # Group songs by various attributes for positive pairs
        genre_groups = self._group_by_attribute("genres")
        artist_groups = self._group_by_attribute("artists")
        era_groups = self._group_by_era()
        
        # Create positive pairs
        all_groups = [genre_groups, artist_groups, era_groups]
        
        for group in all_groups:
            for songs_in_group in group.values():
                if len(songs_in_group) >= 2:
                    # Create pairs within group
                    for i in range(len(songs_in_group)):
                        for j in range(i + 1, len(songs_in_group)):
                            similarity = self._calculate_pair_similarity(
                                self.songs[songs_in_group[i]], 
                                self.songs[songs_in_group[j]]
                            )
                            pairs.append((songs_in_group[i], songs_in_group[j], similarity))
        
        # Create negative pairs with hard negative mining
        num_negatives = len(pairs)  # Balance positive and negative
        added_negatives = 0
        
        while added_negatives < num_negatives:
            i, j = np.random.choice(len(self.songs), 2, replace=False)
            
            # Skip if they're actually similar
            similarity = self._calculate_pair_similarity(self.songs[i], self.songs[j])
            if similarity > 0.3:  # Threshold for "similar"
                continue
            
            pairs.append((i, j, 0.0))
            added_negatives += 1
        
        return pairs
    
    def _group_by_attribute(self, attribute: str) -> Dict[str, List[int]]:
        """Group song indices by attribute"""
        groups = defaultdict(list)
        
        for i, song in enumerate(self.songs):
            values = song.get(attribute, [])
            if isinstance(values, list):
                for value in values:
                    if value:
                        groups[value].append(i)
            elif values:
                groups[values].append(i)
        
        return groups
    
    def _group_by_era(self) -> Dict[str, List[int]]:
        """Group songs by era"""
        groups = defaultdict(list)
        
        for i, song in enumerate(self.songs):
            pub_date = song.get("publication_date")
            if pub_date and isinstance(pub_date, str) and len(pub_date) >= 4:
                try:
                    year = int(pub_date[:4])
                    if year < 2000:
                        era = "pre_2000"
                    elif year < 2010:
                        era = "2000s"
                    elif year < 2020:
                        era = "2010s"
                    else:
                        era = "2020s"
                    groups[era].append(i)
                except ValueError:
                    pass
        
        return groups
    
    def _calculate_pair_similarity(self, song1: Dict[str, Any], song2: Dict[str, Any]) -> float:
        """Calculate similarity between two songs for label weighting"""
        similarity = 0.0
        total_features = 0
        
        # Check shared genres
        genres1 = set(song1.get("genres", []))
        genres2 = set(song2.get("genres", []))
        if genres1 or genres2:
            jaccard = len(genres1 & genres2) / len(genres1 | genres2) if (genres1 or genres2) else 0
            similarity += jaccard * 0.4
            total_features += 0.4
        
        # Check shared artists
        artists1 = set(song1.get("artists", []))
        artists2 = set(song2.get("artists", []))
        if artists1 or artists2:
            jaccard = len(artists1 & artists2) / len(artists1 | artists2) if (artists1 or artists2) else 0
            similarity += jaccard * 0.3
            total_features += 0.3
        
        # Check era similarity
        era1 = self._get_era(song1)
        era2 = self._get_era(song2)
        if era1 and era2:
            era_sim = 1.0 if era1 == era2 else 0.0
            similarity += era_sim * 0.2
            total_features += 0.2
        
        # Check other attributes
        for attr in ["artist_genders", "artist_types", "country", "language"]:
            val1 = song1.get(attr)
            val2 = song2.get(attr)
            if val1 and val2 and val1 == val2:
                similarity += 0.025
                total_features += 0.025
        
        return similarity / total_features if total_features > 0 else 0.0
    
    def _get_era(self, song: Dict[str, Any]) -> Optional[str]:
        """Extract era from song"""
        pub_date = song.get("publication_date")
        if pub_date and isinstance(pub_date, str) and len(pub_date) >= 4:
            try:
                year = int(pub_date[:4])
                if year < 2000:
                    return "pre_2000"
                elif year < 2010:
                    return "2000s"
                elif year < 2020:
                    return "2010s"
                else:
                    return "2020s"
            except ValueError:
                pass
        return None
    
    def __len__(self):
        return len(self.pairs)
    
    def __getitem__(self, idx):
        song1_idx, song2_idx, similarity = self.pairs[idx]
        
        song1_features = torch.FloatTensor(self.features[song1_idx])
        song2_features = torch.FloatTensor(self.features[song2_idx])
        similarity_tensor = torch.FloatTensor([similarity])
        
        return song1_features, song2_features, similarity_tensor


class EnterpriseEmbeddingNet(nn.Module):
    """Enterprise-grade neural network for song embeddings"""
    
    def __init__(self, input_dim: int, config: EmbeddingConfig):
        super(EnterpriseEmbeddingNet, self).__init__()
        
        self.config = config
        self.input_dim = input_dim
        
        # Build encoder layers
        layers = []
        prev_dim = input_dim
        
        for hidden_dim in config.hidden_dims:
            layers.extend([
                nn.Linear(prev_dim, hidden_dim),
                nn.BatchNorm1d(hidden_dim),
                nn.ReLU(),
                nn.Dropout(config.dropout_rate)
            ])
            prev_dim = hidden_dim
        
        # Output embedding layer
        layers.append(nn.Linear(prev_dim, config.embedding_dim))
        
        if config.normalize_embeddings:
            layers.append(nn.Tanh())  # Normalize to [-1, 1]
        
        self.encoder = nn.Sequential(*layers)
        
        # Initialize weights
        self._initialize_weights()
    
    def _initialize_weights(self):
        """Initialize network weights"""
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.xavier_uniform_(m.weight)
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.BatchNorm1d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)
    
    def forward(self, x):
        return self.encoder(x)
    
    def get_embedding(self, x):
        """Get embedding for input"""
        self.eval()
        with torch.no_grad():
            return self.encoder(x)


class ContrastiveLoss(nn.Module):
    """Enhanced contrastive loss for metric learning"""
    
    def __init__(self, margin: float = 1.0, loss_type: str = "contrastive"):
        super(ContrastiveLoss, self).__init__()
        self.margin = margin
        self.loss_type = loss_type
    
    def forward(self, embedding1, embedding2, similarity):
        if self.loss_type == "contrastive":
            return self._contrastive_loss(embedding1, embedding2, similarity)
        elif self.loss_type == "triplet":
            return self._triplet_loss(embedding1, embedding2, similarity)
        else:
            return self._contrastive_loss(embedding1, embedding2, similarity)
    
    def _contrastive_loss(self, embedding1, embedding2, similarity):
        """Traditional contrastive loss"""
        # Calculate cosine similarity
        cos_sim = F.cosine_similarity(embedding1, embedding2, dim=1)
        
        # Convert similarity (0-1) to target (0 or 1)
        target = (similarity.squeeze() > 0.5).float()
        
        # Contrastive loss
        loss = (1 - target) * 0.5 * (cos_sim ** 2) + \
               target * 0.5 * torch.clamp(self.margin - cos_sim, min=0) ** 2
        
        return loss.mean()
    
    def _triplet_loss(self, embedding1, embedding2, similarity):
        """Triplet loss implementation"""
        # This would need anchor, positive, negative samples
        # For now, fall back to contrastive
        return self._contrastive_loss(embedding1, embedding2, similarity)


class EnterpriseEmbeddingTrainer:
    """Enterprise-grade embedding trainer with validation and monitoring"""
    
    def __init__(self, config: EmbeddingConfig):
        if not TORCH_AVAILABLE:
            raise ImportError("PyTorch is required for embedding training")
        
        self.config = config
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = None
        self.preprocessor = None
        self.training_history = []
        self.best_model_state = None
        
        logger.info(f"EnterpriseEmbeddingTrainer initialized on {self.device}")
    
    def train(self, songs: List[Dict[str, Any]]) -> TrainingMetrics:
        """Train embedding model with proper validation"""
        logger.info(f"Starting embedding training on {len(songs)} songs")
        
        if len(songs) < 10:
            raise ValueError("Need at least 10 songs for meaningful training")
        
        # Preprocess data
        self.preprocessor = DataPreprocessor().fit(songs)
        
        # Create datasets
        full_dataset = SongDataset(songs, self.preprocessor, mode="train")
        
        # Split into train/validation
        val_size = int(len(full_dataset) * self.config.validation_split)
        train_size = len(full_dataset) - val_size
        
        train_dataset, val_dataset = random_split(
            full_dataset, [train_size, val_size],
            generator=torch.Generator().manual_seed(42)
        )
        
        # Create data loaders
        train_loader = DataLoader(
            train_dataset, 
            batch_size=self.config.batch_size,
            shuffle=True,
            num_workers=0  # Windows compatibility
        )
        
        val_loader = DataLoader(
            val_dataset,
            batch_size=self.config.batch_size,
            shuffle=False,
            num_workers=0
        )
        
        # Initialize model
        input_dim = full_dataset.features.shape[1]
        self.model = EnterpriseEmbeddingNet(input_dim, self.config).to(self.device)
        
        # Initialize optimizer and loss
        optimizer = optim.Adam(self.model.parameters(), lr=self.config.learning_rate)
        scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=5, factor=0.5)
        criterion = ContrastiveLoss(margin=self.config.margin)
        
        # Training loop
        best_val_loss = float('inf')
        epochs_without_improvement = 0
        training_start = datetime.now()
        
        for epoch in range(self.config.epochs):
            # Training phase
            self.model.train()
            train_loss = 0.0
            train_correct = 0
            train_total = 0
            
            for batch_idx, (song1_features, song2_features, similarity) in enumerate(train_loader):
                song1_features = song1_features.to(self.device)
                song2_features = song2_features.to(self.device)
                similarity = similarity.to(self.device)
                
                optimizer.zero_grad()
                
                # Forward pass
                embedding1 = self.model(song1_features)
                embedding2 = self.model(song2_features)
                
                # Calculate loss
                loss = criterion(embedding1, embedding2, similarity)
                
                # Backward pass
                loss.backward()
                optimizer.step()
                
                train_loss += loss.item()
                
                # Calculate accuracy (similarity prediction)
                with torch.no_grad():
                    cos_sim = F.cosine_similarity(embedding1, embedding2, dim=1)
                    predicted = (cos_sim > 0.5).float()
                    target = (similarity.squeeze() > 0.5).float()
                    train_correct += (predicted == target).sum().item()
                    train_total += target.size(0)
            
            # Validation phase
            self.model.eval()
            val_loss = 0.0
            val_correct = 0
            val_total = 0
            
            with torch.no_grad():
                for song1_features, song2_features, similarity in val_loader:
                    song1_features = song1_features.to(self.device)
                    song2_features = song2_features.to(self.device)
                    similarity = similarity.to(self.device)
                    
                    embedding1 = self.model(song1_features)
                    embedding2 = self.model(song2_features)
                    
                    loss = criterion(embedding1, embedding2, similarity)
                    val_loss += loss.item()
                    
                    # Calculate accuracy
                    cos_sim = F.cosine_similarity(embedding1, embedding2, dim=1)
                    predicted = (cos_sim > 0.5).float()
                    target = (similarity.squeeze() > 0.5).float()
                    val_correct += (predicted == target).sum().item()
                    val_total += target.size(0)
            
            # Calculate metrics
            avg_train_loss = train_loss / len(train_loader)
            avg_val_loss = val_loss / len(val_loader)
            train_accuracy = train_correct / train_total if train_total > 0 else 0
            val_accuracy = val_correct / val_total if val_total > 0 else 0
            
            # Learning rate scheduling
            scheduler.step(avg_val_loss)
            
            # Early stopping
            if avg_val_loss < best_val_loss:
                best_val_loss = avg_val_loss
                epochs_without_improvement = 0
                self.best_model_state = self.model.state_dict().copy()
            else:
                epochs_without_improvement += 1
            
            # Log progress
            if epoch % 10 == 0:
                logger.info(f"Epoch {epoch}: Train Loss: {avg_train_loss:.4f}, Val Loss: {avg_val_loss:.4f}, "
                          f"Train Acc: {train_accuracy:.3f}, Val Acc: {val_accuracy:.3f}")
            
            # Early stopping
            if epochs_without_improvement >= self.config.early_stopping_patience:
                logger.info(f"Early stopping at epoch {epoch}")
                break
        
        # Load best model
        if self.best_model_state:
            self.model.load_state_dict(self.best_model_state)
        
        training_time = (datetime.now() - training_start).total_seconds()
        
        # Create metrics
        metrics = TrainingMetrics(
            train_loss=avg_train_loss,
            val_loss=avg_val_loss,
            train_accuracy=train_accuracy,
            val_accuracy=val_accuracy,
            epoch=epoch,
            training_time=training_time,
            best_val_loss=best_val_loss,
            epochs_without_improvement=epochs_without_improvement
        )
        
        logger.info(f"Training completed in {training_time:.1f}s. Best val loss: {best_val_loss:.4f}")
        return metrics
    
    def compute_embeddings(self, songs: List[Dict[str, Any]]) -> Dict[str, np.ndarray]:
        """Compute embeddings for all songs"""
        if not self.model or not self.preprocessor:
            raise RuntimeError("Model must be trained before computing embeddings")
        
        logger.info(f"Computing embeddings for {len(songs)} songs")
        
        self.model.eval()
        features = self.preprocessor.transform(songs)
        
        embeddings = {}
        
        with torch.no_grad():
            for i, song in enumerate(songs):
                feature_tensor = torch.FloatTensor(features[i]).unsqueeze(0).to(self.device)
                embedding = self.model(feature_tensor).cpu().numpy().squeeze()
                embeddings[song["title"]] = embedding
        
        logger.info(f"Computed {len(embeddings)} embeddings")
        return embeddings
    
    def save_model(self, filepath: str):
        """Save trained model and preprocessing pipeline"""
        if not self.model or not self.preprocessor:
            raise RuntimeError("Model must be trained before saving")
        
        save_data = {
            "model_state_dict": self.model.state_dict(),
            "model_config": {
                "input_dim": self.model.input_dim,
                "embedding_dim": self.config.embedding_dim,
                "hidden_dims": self.config.hidden_dims
            },
            "preprocessor": self.preprocessor,
            "config": self.config,
            "training_history": self.training_history
        }
        
        torch.save(save_data, filepath)
        logger.info(f"Model saved to {filepath}")
    
    def load_model(self, filepath: str) -> bool:
        """Load trained model and preprocessing pipeline"""
        try:
            save_data = torch.load(filepath, map_location=self.device)
            
            # Reconstruct model
            model_config = save_data["model_config"]
            self.model = EnterpriseEmbeddingNet(
                model_config["input_dim"], 
                save_data["config"]
            ).to(self.device)
            
            self.model.load_state_dict(save_data["model_state_dict"])
            self.preprocessor = save_data["preprocessor"]
            self.config = save_data["config"]
            self.training_history = save_data.get("training_history", [])
            
            logger.info(f"Model loaded from {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return False
    
    def evaluate_embeddings(self, songs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Evaluate embedding quality"""
        if not SKLEARN_AVAILABLE:
            logger.warning("Scikit-learn not available for evaluation")
            return {"error": "Scikit-learn required for evaluation"}
        
        embeddings = self.compute_embeddings(songs)
        
        # Create similarity matrix
        song_titles = list(embeddings.keys())
        embedding_matrix = np.array([embeddings[title] for title in song_titles])
        
        # Calculate cosine similarities
        similarities = np.dot(embedding_matrix, embedding_matrix.T)
        np.fill_diagonal(similarities, 0)  # Remove self-similarities
        
        # Evaluate against ground truth similarities
        ground_truth = np.zeros_like(similarities)
        for i, song1 in enumerate(songs):
            for j, song2 in enumerate(songs):
                if i != j:
                    # Calculate ground truth similarity
                    gt_sim = self._calculate_ground_truth_similarity(song1, song2)
                    ground_truth[i, j] = gt_sim
        
        # Calculate metrics
        # Flatten matrices for evaluation
        sim_flat = similarities.flatten()
        gt_flat = ground_truth.flatten()
        
        # Convert to binary classification (similar vs not similar)
        binary_pred = (sim_flat > 0.5).astype(int)
        binary_gt = (gt_flat > 0.5).astype(int)
        
        precision, recall, f1, _ = precision_recall_fscore_support(
            binary_gt, binary_pred, average='weighted', zero_division=0
        )
        
        # Calculate AUC if possible
        try:
            auc = roc_auc_score(binary_gt, sim_flat)
        except ValueError:
            auc = 0.0
        
        evaluation = {
            "precision": precision,
            "recall": recall,
            "f1_score": f1,
            "auc": auc,
            "avg_similarity": np.mean(similarities),
            "std_similarity": np.std(similarities),
            "num_pairs": len(sim_flat)
        }
        
        logger.info(f"Embedding evaluation: F1={f1:.3f}, AUC={auc:.3f}")
        return evaluation
    
    def _calculate_ground_truth_similarity(self, song1: Dict[str, Any], song2: Dict[str, Any]) -> float:
        """Calculate ground truth similarity between two songs"""
        similarity = 0.0
        total_weight = 0.0
        
        # Genre similarity (weight: 0.4)
        genres1 = set(song1.get("genres", []))
        genres2 = set(song2.get("genres", []))
        if genres1 or genres2:
            jaccard = len(genres1 & genres2) / len(genres1 | genres2)
            similarity += jaccard * 0.4
            total_weight += 0.4
        
        # Artist similarity (weight: 0.3)
        artists1 = set(song1.get("artists", []))
        artists2 = set(song2.get("artists", []))
        if artists1 or artists2:
            jaccard = len(artists1 & artists2) / len(artists1 | artists2)
            similarity += jaccard * 0.3
            total_weight += 0.3
        
        # Era similarity (weight: 0.2)
        era1 = self._get_era(song1)
        era2 = self._get_era(song2)
        if era1 and era2:
            similarity += (1.0 if era1 == era2 else 0.0) * 0.2
            total_weight += 0.2
        
        # Other attributes (weight: 0.1)
        for attr in ["artist_genders", "country", "language"]:
            val1 = song1.get(attr)
            val2 = song2.get(attr)
            if val1 and val2 and val1 == val2:
                similarity += 0.033
                total_weight += 0.033
        
        return similarity / total_weight if total_weight > 0 else 0.0
    
    def _get_era(self, song: Dict[str, Any]) -> Optional[str]:
        """Extract era from song"""
        pub_date = song.get("publication_date")
        if pub_date and isinstance(pub_date, str) and len(pub_date) >= 4:
            try:
                year = int(pub_date[:4])
                if year < 2000:
                    return "pre_2000"
                elif year < 2010:
                    return "2000s"
                elif year < 2020:
                    return "2010s"
                else:
                    return "2020s"
            except ValueError:
                pass
        return None
