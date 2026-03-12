#!/usr/bin/env python3
"""
Hybrid System Setup and Verification
Sets up and tests the complete hybrid intelligence system
"""

import sys
import os
import json

# Add the backend directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def check_dependencies():
    """Check if all dependencies are available"""
    print("🔍 Checking dependencies...")
    
    missing = []
    
    # Check PyTorch
    try:
        import torch
        print("✅ PyTorch available")
    except ImportError:
        missing.append("PyTorch")
        print("❌ PyTorch missing (pip install torch)")
    
    # Check NumPy
    try:
        import numpy
        print("✅ NumPy available")
    except ImportError:
        missing.append("NumPy")
        print("❌ NumPy missing (pip install numpy)")
    
    # Check Flask
    try:
        import flask
        print("✅ Flask available")
    except ImportError:
        missing.append("Flask")
        print("❌ Flask missing (pip install flask)")
    
    return missing

def setup_embeddings():
    """Setup neural embeddings if available"""
    try:
        import torch
        import numpy
        
        print("\n🧠 Setting up neural embeddings...")
        
        from backend.logic.kg_loader import load_dataset
        from backend.logic.embeddings import train_embeddings
        
        # Load dataset
        songs = load_dataset()
        print(f"📊 Loaded {len(songs)} songs for training")
        
        if len(songs) < 10:
            print("⚠️ Need at least 10 songs for meaningful embeddings")
            return False
        
        # Train embeddings
        print("🏋️ Training neural embeddings (this may take a few minutes)...")
        trainer = train_embeddings(songs, epochs=50)  # Reduced epochs for faster setup
        
        # Save model
        model_path = os.path.join(os.path.dirname(__file__), 'backend', 'data', 'song_embeddings.pt')
        trainer.save_model(model_path)
        
        print(f"✅ Embeddings trained and saved to {model_path}")
        return True
        
    except Exception as e:
        print(f"❌ Embedding setup failed: {e}")
        return False

def setup_dynamic_graph():
    """Setup dynamic Wikidata graph"""
    try:
        print("\n🌐 Setting up dynamic Wikidata graph...")
        
        from backend.logic.dynamic_graph import build_dynamic_graph
        
        # Build graph
        graph = build_dynamic_graph(limit=100)  # Smaller for faster setup
        
        # Save graph
        graph_path = os.path.join(os.path.dirname(__file__), 'backend', 'data', 'dynamic_graph.json')
        graph.save_graph(graph_path)
        
        print(f"✅ Dynamic graph built and saved to {graph_path}")
        print(f"   Songs: {len(graph.graph['songs'])}")
        print(f"   Attribute types: {len(graph.graph['attributes'])}")
        
        return True
        
    except Exception as e:
        print(f"❌ Dynamic graph setup failed: {e}")
        return False

def test_hybrid_engine():
    """Test the hybrid engine"""
    try:
        print("\n🧪 Testing hybrid engine...")
        
        from backend.logic.hybrid_engine import create_hybrid_engine
        
        # Create hybrid engine
        engine = create_hybrid_engine(enable_graph=True, enable_embeddings=True)
        
        print(f"✅ Hybrid engine created successfully")
        
        # Get system status
        status = engine.get_system_status()
        print(f"   Graph available: {status['graph_available']}")
        print(f"   Embeddings available: {status['embedding_available']}")
        print(f"   Total songs: {status['total_songs']}")
        print(f"   Total questions: {status['total_questions']}")
        
        # Test question generation
        candidate_songs = [song["title"] for song in engine.get_entities()[:5]]
        asked = set()
        
        question = engine.get_optimal_question(candidate_songs, asked)
        if question:
            print(f"✅ Question generation working: {question.get('text', 'N/A')}")
        else:
            print("⚠️ Question generation returned None")
        
        # Test similarity calculation
        if len(candidate_songs) >= 2:
            similarity = engine.calculate_similarity(candidate_songs[0], candidate_songs[1])
            print(f"✅ Similarity calculation working: {similarity:.3f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Hybrid engine test failed: {e}")
        return False

def create_configuration():
    """Create optimal configuration file"""
    config = {
        "hybrid_mode": {
            "enable_graph": True,
            "enable_embeddings": True,
            "graph_weight": 0.6,
            "embedding_weight": 0.4
        },
        "performance": {
            "max_candidates": 10,
            "cache_results": True,
            "parallel_processing": False
        },
        "robustness": {
            "fallback_to_tags": True,
            "auto_retry_failed_questions": True,
            "minimum_confidence": 0.3
        },
        "learning": {
            "smart_learning_enabled": True,
            "quality_threshold": 0.3,
            "auto_improve": True
        }
    }
    
    config_path = os.path.join(os.path.dirname(__file__), 'hybrid_config.json')
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"✅ Configuration saved to {config_path}")
    return config_path

def main():
    """Main setup function"""
    print("🚀 Hybrid Music Akenator Setup")
    print("=" * 50)
    
    # Check dependencies
    missing_deps = check_dependencies()
    if missing_deps:
        print(f"\n❌ Missing dependencies: {', '.join(missing_deps)}")
        print("Install them with: pip install " + " ".join(missing_deps))
        return False
    
    # Create configuration
    config_path = create_configuration()
    
    # Setup components
    success = True
    
    # Always try to setup graph (more reliable)
    if not setup_dynamic_graph():
        success = False
    
    # Setup embeddings if PyTorch is available
    if 'torch' not in missing_deps:
        if not setup_embeddings():
            print("⚠️ Embeddings setup failed, but graph system should work")
    
    # Test the hybrid system
    if not test_hybrid_engine():
        success = False
    
    if success:
        print("\n🎉 Hybrid system setup complete!")
        print("\n📋 Next steps:")
        print("1. Start the backend: python app.py")
        print("2. Start the frontend: cd song-genie-ui && npm run dev")
        print("3. Visit: http://localhost:3000")
        print("\n🔧 Available modes:")
        print("- Graph only: http://localhost:3000?graph=true&embeddings=false")
        print("- Embeddings only: http://localhost:3000?graph=false&embeddings=true")
        print("- Hybrid (recommended): http://localhost:3000?graph=true&embeddings=true")
    else:
        print("\n❌ Setup completed with issues. Check the error messages above.")
    
    return success

if __name__ == "__main__":
    main()
