"""
Debug Visualization Tools
Graph and embedding visualization for system understanding
"""

import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import List, Dict, Any, Optional
import logging
import networkx as nx
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
import pandas as pd

logger = logging.getLogger(__name__)

class GraphVisualizer:
    """Visualize knowledge graph structure and relationships"""
    
    def __init__(self, graph_intelligence=None):
        self.graph_intelligence = graph_intelligence
    
    def create_graph_visualization(self, output_file: str = "knowledge_graph.png", 
                             max_nodes: int = 50):
        """Create comprehensive graph visualization"""
        if not self.graph_intelligence:
            logger.warning("No graph intelligence available for visualization")
            return
        
        logger.info(f"📊 Creating graph visualization with max {max_nodes} nodes")
        
        # Get graph from intelligence system
        graph = self.graph_intelligence.graph
        
        # Create subgraph with limited nodes for readability
        all_nodes = list(graph.nodes())
        
        # Prioritize important nodes (high centrality)
        node_importance = {}
        for node in all_nodes:
            if node.startswith('song_'):
                continue  # Skip song nodes for importance calculation
            
            centrality = self.graph_intelligence.get_attribute_centrality(
                node.split('_', 1)[0], 
                node.split('_', 1)[1].replace('_', ' ')
            )
            node_importance[node] = centrality.get('betweenness', 0)
        
        # Sort by importance and take top nodes
        important_nodes = sorted(node_importance.items(), key=lambda x: x[1], reverse=True)
        selected_nodes = [node for node, _ in important_nodes[:max_nodes//2]]
        
        # Add connected song nodes
        for node in selected_nodes:
            neighbors = list(graph.neighbors(node))
            for neighbor in neighbors:
                if neighbor.startswith('song_') and len(selected_nodes) < max_nodes:
                    selected_nodes.append(neighbor)
        
        # Create subgraph
        subgraph = graph.subgraph(selected_nodes)
        
        # Create visualization
        plt.figure(figsize=(16, 12))
        pos = nx.spring_layout(subgraph, k=2, iterations=50)
        
        # Separate node types
        song_nodes = [n for n in subgraph.nodes() if n.startswith('song_')]
        attr_nodes = [n for n in subgraph.nodes() if not n.startswith('song_')]
        
        # Draw edges
        nx.draw_networkx_edges(subgraph, pos, alpha=0.3, edge_color='gray', width=0.5)
        
        # Draw attribute nodes
        nx.draw_networkx_nodes(subgraph, pos, nodelist=attr_nodes, 
                             node_color='lightgreen', node_size=800, alpha=0.8,
                             font_size=8, font_weight='bold')
        
        # Draw song nodes
        nx.draw_networkx_nodes(subgraph, pos, nodelist=song_nodes, 
                             node_color='lightblue', node_size=300, alpha=0.7)
        
        # Add labels for important nodes
        important_attr_nodes = [n for n in attr_nodes if n in [node for node, _ in important_nodes[:10]]]
        labels = {node: node.replace('_', ' ').replace('song_', 'Song ') for node in important_attr_nodes}
        nx.draw_networkx_labels(subgraph, pos, labels=labels, font_size=8, font_color='darkred')
        
        plt.title("Music Akenator Knowledge Graph\n(Green: Attributes, Blue: Songs)", fontsize=14)
        plt.axis('off')
        plt.tight_layout()
        plt.savefig(output_file, dpi=150, bbox_inches='tight')
        plt.close()
        
        logger.info(f"📊 Graph visualization saved to {output_file}")
    
    def create_attribute_analysis(self, output_file: str = "attribute_analysis.png"):
        """Create visualization of attribute distribution and importance"""
        if not self.graph_intelligence:
            return
        
        logger.info("📊 Creating attribute analysis visualization")
        
        # Get attribute statistics
        graph_stats = self.graph_intelligence.get_graph_statistics()
        
        # Create subplots
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle("Knowledge Graph Analysis", fontsize=16)
        
        # 1. Node type distribution
        node_types = ['Song Nodes', 'Attribute Nodes']
        node_counts = [graph_stats['song_nodes'], graph_stats['attribute_nodes']]
        
        axes[0, 0].bar(node_types, node_counts, color=['lightblue', 'lightgreen'])
        axes[0, 0].set_title('Node Distribution')
        axes[0, 0].set_ylabel('Count')
        
        # 2. Graph density
        axes[0, 1].bar(['Density'], [graph_stats['density']], color='orange')
        axes[0, 1].set_title('Graph Density')
        axes[0, 1].set_ylabel('Density Value')
        
        # 3. Connectivity
        connectivity_data = ['Connected', 'Components']
        connectivity_values = [1 if graph_stats['is_connected'] else 0, 
                          nx.number_connected_components(self.graph_intelligence.graph)]
        
        axes[1, 0].bar(connectivity_data, connectivity_values, color=['purple', 'pink'])
        axes[1, 0].set_title('Graph Connectivity')
        axes[1, 0].set_ylabel('Value')
        
        # 4. Clustering coefficient
        axes[1, 1].bar(['Avg Clustering'], [graph_stats['average_clustering']], color='brown')
        axes[1, 1].set_title('Clustering Coefficient')
        axes[1, 1].set_ylabel('Clustering Value')
        
        plt.tight_layout()
        plt.savefig(output_file, dpi=150, bbox_inches='tight')
        plt.close()
        
        logger.info(f"📊 Attribute analysis saved to {output_file}")


class EmbeddingVisualizer:
    """Visualize neural embeddings and song clusters"""
    
    def __init__(self, embedding_trainer=None):
        self.embedding_trainer = embedding_trainer
    
    def create_embedding_visualization(self, output_file: str = "embedding_clusters.png",
                                 method: str = "pca"):
        """Create 2D visualization of song embeddings"""
        if not self.embedding_trainer or not hasattr(self.embedding_trainer, 'embeddings'):
            logger.warning("No embeddings available for visualization")
            return
        
        logger.info(f"🎯 Creating embedding visualization using {method.upper()}")
        
        embeddings = self.embedding_trainer.embeddings
        songs = self.embedding_trainer.song_metadata
        
        # Reduce to 2D
        if method.lower() == "pca":
            embeddings_2d = self._pca_reduction(embeddings)
        elif method.lower() == "tsne":
            embeddings_2d = self._tsne_reduction(embeddings)
        else:
            embeddings_2d = self._pca_reduction(embeddings)  # Default to PCA
        
        # Create visualization
        plt.figure(figsize=(14, 10))
        
        # Get genres for coloring
        genres = []
        for song in songs:
            song_genres = song.get('genres', [])
            genres.append(song_genres[0] if song_genres else 'Unknown')
        
        # Create scatter plot
        unique_genres = list(set(genres))
        colors = plt.cm.Set3(np.linspace(0, 1, len(unique_genres)))
        
        for i, genre in enumerate(unique_genres):
            genre_mask = [g == genre for g in genres]
            genre_embeddings = embeddings_2d[genre_mask]
            
            plt.scatter(genre_embeddings[:, 0], genre_embeddings[:, 1], 
                       c=[colors[i]], label=genre, alpha=0.7, s=50)
        
        plt.title(f"Song Embeddings Visualization ({method.upper()})", fontsize=16)
        plt.xlabel("Component 1", fontsize=12)
        plt.ylabel("Component 2", fontsize=12)
        
        # Add legend
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(output_file, dpi=150, bbox_inches='tight')
        plt.close()
        
        logger.info(f"🎯 Embedding visualization saved to {output_file}")
    
    def _pca_reduction(self, embeddings: np.ndarray) -> np.ndarray:
        """Reduce embeddings using PCA"""
        pca = PCA(n_components=2, random_state=42)
        embeddings_2d = pca.fit_transform(embeddings)
        
        logger.info(f"PCA explained variance: {pca.explained_variance_ratio_.sum():.3f}")
        return embeddings_2d
    
    def _tsne_reduction(self, embeddings: np.ndarray) -> np.ndarray:
        """Reduce embeddings using t-SNE"""
        tsne = TSNE(n_components=2, random_state=42, perplexity=min(30, len(embeddings)-1))
        embeddings_2d = tsne.fit_transform(embeddings)
        return embeddings_2d
    
    def create_similarity_heatmap(self, output_file: str = "similarity_heatmap.png",
                              sample_size: int = 20):
        """Create heatmap of song similarities"""
        if not self.embedding_trainer:
            return
        
        logger.info(f"🔥 Creating similarity heatmap for {sample_size} songs")
        
        embeddings = self.embedding_trainer.embeddings[:sample_size]
        songs = self.embedding_trainer.song_metadata[:sample_size]
        
        # Calculate similarity matrix
        similarity_matrix = np.zeros((sample_size, sample_size))
        for i in range(sample_size):
            for j in range(sample_size):
                if i != j:
                    similarity_matrix[i, j] = np.dot(embeddings[i], embeddings[j]) / (
                        np.linalg.norm(embeddings[i]) * np.linalg.norm(embeddings[j])
                    )
        
        # Get song titles for labels
        titles = [song.get('title', f'Song {i}')[:15] + '...' if len(song.get('title', '')) > 15 else song.get('title', f'Song {i}') 
                   for i, song in enumerate(songs)]
        
        # Create heatmap
        plt.figure(figsize=(12, 10))
        
        # Mask diagonal for better visualization
        mask = np.zeros_like(similarity_matrix, dtype=bool)
        np.fill_diagonal(mask, True)
        
        sns.heatmap(similarity_matrix, 
                   xticklabels=titles, 
                   yticklabels=titles,
                   mask=mask,
                   cmap='viridis',
                   center=0,
                   annot=True if sample_size <= 15 else False,
                   fmt='.2f' if sample_size <= 15 else None)
        
        plt.title("Song Similarity Heatmap", fontsize=16)
        plt.xlabel("Songs", fontsize=12)
        plt.ylabel("Songs", fontsize=12)
        plt.xticks(rotation=45, ha='right')
        plt.yticks(rotation=0)
        
        plt.tight_layout()
        plt.savefig(output_file, dpi=150, bbox_inches='tight')
        plt.close()
        
        logger.info(f"🔥 Similarity heatmap saved to {output_file}")
    
    def create_genre_distribution_plot(self, output_file: str = "genre_distribution.png"):
        """Create visualization of genre distribution in embedding space"""
        if not self.embedding_trainer:
            return
        
        logger.info("🎵 Creating genre distribution visualization")
        
        embeddings = self.embedding_trainer.embeddings
        songs = self.embedding_trainer.song_metadata
        
        # Extract genres and create embeddings by genre
        genre_embeddings = {}
        for song, embedding in zip(songs, embeddings):
            genres = song.get('genres', [])
            if genres:
                primary_genre = genres[0]
                if primary_genre not in genre_embeddings:
                    genre_embeddings[primary_genre] = []
                genre_embeddings[primary_genre].append(embedding)
        
        # Calculate genre centroids
        genre_centroids = {}
        for genre, emb_list in genre_embeddings.items():
            if emb_list:
                genre_centroids[genre] = np.mean(emb_list, axis=0)
        
        # Create visualization
        plt.figure(figsize=(14, 10))
        
        if genre_centroids:
            # Plot genre centroids
            genres = list(genre_centroids.keys())
            centroids = np.array(list(genre_centroids.values()))
            
            # Use PCA for visualization if needed
            if centroids.shape[1] > 2:
                pca = PCA(n_components=2, random_state=42)
                centroids_2d = pca.fit_transform(centroids)
            else:
                centroids_2d = centroids
            
            plt.scatter(centroids_2d[:, 0], centroids_2d[:, 1], 
                       s=200, alpha=0.8, c=range(len(genres)))
            
            # Add labels
            for i, genre in enumerate(genres):
                plt.annotate(genre, (centroids_2d[i, 0], centroids_2d[i, 1]), 
                           fontsize=10, fontweight='bold')
        
        plt.title("Genre Distribution in Embedding Space", fontsize=16)
        plt.xlabel("Component 1", fontsize=12)
        plt.ylabel("Component 2", fontsize=12)
        plt.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(output_file, dpi=150, bbox_inches='tight')
        plt.close()
        
        logger.info(f"🎵 Genre distribution saved to {output_file}")


class SystemVisualizer:
    """Combined visualization system for all components"""
    
    def __init__(self, graph_intelligence=None, embedding_trainer=None):
        self.graph_viz = GraphVisualizer(graph_intelligence)
        self.embedding_viz = EmbeddingVisualizer(embedding_trainer)
    
    def create_comprehensive_visualization(self, output_dir: str = "visualizations"):
        """Create all visualization types"""
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        logger.info("🎨 Creating comprehensive system visualization...")
        
        # Graph visualizations
        try:
            self.graph_viz.create_graph_visualization(
                f"{output_dir}/knowledge_graph.png"
            )
            self.graph_viz.create_attribute_analysis(
                f"{output_dir}/attribute_analysis.png"
            )
        except Exception as e:
            logger.warning(f"Graph visualization failed: {e}")
        
        # Embedding visualizations
        try:
            self.embedding_viz.create_embedding_visualization(
                f"{output_dir}/embedding_clusters_pca.png", "pca"
            )
            self.embedding_viz.create_embedding_visualization(
                f"{output_dir}/embedding_clusters_tsne.png", "tsne"
            )
            self.embedding_viz.create_similarity_heatmap(
                f"{output_dir}/similarity_heatmap.png"
            )
            self.embedding_viz.create_genre_distribution_plot(
                f"{output_dir}/genre_distribution.png"
            )
        except Exception as e:
            logger.warning(f"Embedding visualization failed: {e}")
        
        logger.info(f"🎨 All visualizations saved to {output_dir}/")
    
    def create_performance_dashboard(self, evaluation_results: Dict[str, Any], 
                               output_file: str = "performance_dashboard.png"):
        """Create performance dashboard from evaluation results"""
        logger.info("📊 Creating performance dashboard...")
        
        # Create subplots
        fig, axes = plt.subplots(2, 3, figsize=(18, 12))
        fig.suptitle("Music Akenator Performance Dashboard", fontsize=16)
        
        # 1. Success rate
        game_metrics = evaluation_results.get('game_simulation', {}).get('metrics', {})
        success_rate = game_metrics.get('success_rate', 0)
        
        axes[0, 0].bar(['Success Rate'], [success_rate], color='green' if success_rate > 0.7 else 'orange')
        axes[0, 0].set_title('Game Success Rate')
        axes[0, 0].set_ylabel('Rate')
        axes[0, 0].set_ylim(0, 1)
        
        # 2. Average questions
        avg_questions = game_metrics.get('avg_questions', 0)
        
        axes[0, 1].bar(['Avg Questions'], [avg_questions], color='blue' if avg_questions < 10 else 'red')
        axes[0, 1].set_title('Average Questions per Game')
        axes[0, 1].set_ylabel('Questions')
        
        # 3. Confidence distribution
        entropy_reductions = game_metrics.get('entropy_reduction', [])
        if entropy_reductions:
            axes[0, 2].hist(entropy_reductions, bins=20, alpha=0.7, color='purple')
            axes[0, 2].set_title('Entropy Reduction Distribution')
            axes[0, 2].set_xlabel('Entropy Reduction')
            axes[0, 2].set_ylabel('Frequency')
        
        # 4. Dataset size
        dataset_stats = evaluation_results.get('dataset_stats', {})
        total_songs = dataset_stats.get('total_songs', 0)
        
        axes[1, 0].bar(['Total Songs'], [total_songs], color='cyan')
        axes[1, 0].set_title('Dataset Size')
        axes[1, 0].set_ylabel('Number of Songs')
        
        # 5. Attribute coverage
        attribute_coverage = dataset_stats.get('attribute_coverage', {})
        if attribute_coverage:
            attrs = list(attribute_coverage.keys())[:5]  # Top 5 attributes
            coverage = [attribute_coverage.get(attr, 0) for attr in attrs]
            
            axes[1, 1].bar(attrs, coverage, color='orange')
            axes[1, 1].set_title('Attribute Coverage')
            axes[1, 1].set_ylabel('Coverage Rate')
            axes[1, 1].tick_params(axis='x', rotation=45)
        
        # 6. Recommendations
        recommendations = evaluation_results.get('recommendations', [])
        
        axes[1, 2].axis('off')
        if recommendations:
            rec_text = '\n'.join(f"• {rec}" for rec in recommendations[:5])
            axes[1, 2].text(0.1, 0.5, rec_text, fontsize=10, 
                           verticalalignment='top', transform=axes[1, 2].transAxes)
            axes[1, 2].set_title('Recommendations')
        
        plt.tight_layout()
        plt.savefig(output_file, dpi=150, bbox_inches='tight')
        plt.close()
        
        logger.info(f"📊 Performance dashboard saved to {output_file}")


def create_system_visualizer(graph_intelligence=None, embedding_trainer=None) -> SystemVisualizer:
    """Factory function to create system visualizer"""
    return SystemVisualizer(graph_intelligence, embedding_trainer)
