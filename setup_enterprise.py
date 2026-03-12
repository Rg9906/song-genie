#!/usr/bin/env python3
"""
Enterprise Music Akenator Setup Script
Complete setup and verification of the enterprise-grade system
"""

import os
import sys
import json
import logging
import argparse
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional
import time

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.logic.testing_framework import run_comprehensive_tests
from backend.logic.dataset_pipeline import DatasetPipeline, PipelineConfig
from backend.logic.performance_monitor import get_performance_monitor

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class EnterpriseSetup:
    """Complete enterprise setup and verification"""
    
    def __init__(self, data_dir: str = None):
        self.data_dir = data_dir or os.path.join(os.path.dirname(__file__), 'backend', 'data')
        self.setup_steps = []
        self.results = {}
        
        # Ensure data directory exists
        os.makedirs(self.data_dir, exist_ok=True)
        
        logger.info(f"Enterprise setup initialized with data directory: {self.data_dir}")
    
    def check_dependencies(self) -> bool:
        """Check all required dependencies"""
        logger.info("🔍 Checking dependencies...")
        
        required_packages = [
            'flask', 'flask-cors', 'requests', 'numpy', 
            'networkx', 'psutil'
        ]
        
        optional_packages = [
            'torch', 'torchvision', 'sklearn', 'matplotlib'
        ]
        
        missing_required = []
        missing_optional = []
        
        for package in required_packages:
            try:
                __import__(package)
                logger.info(f"✅ {package}")
            except ImportError:
                missing_required.append(package)
                logger.error(f"❌ {package} (required)")
        
        for package in optional_packages:
            try:
                __import__(package)
                logger.info(f"✅ {package} (optional)")
            except ImportError:
                missing_optional.append(package)
                logger.warning(f"⚠️ {package} (optional)")
        
        if missing_required:
            logger.error(f"Missing required packages: {', '.join(missing_required)}")
            logger.info("Install with: pip install " + " ".join(missing_required))
            return False
        
        if missing_optional:
            logger.info(f"Missing optional packages: {', '.join(missing_optional)}")
            logger.info("Install with: pip install " + " ".join(missing_optional))
        
        self.results['dependencies'] = {
            'required_missing': missing_required,
            'optional_missing': missing_optional,
            'success': len(missing_required) == 0
        }
        
        return len(missing_required) == 0
    
    def setup_data_directory(self) -> bool:
        """Setup data directory structure"""
        logger.info("📁 Setting up data directory...")
        
        try:
            # Create necessary directories
            directories = [
                self.data_dir,
                os.path.join(self.data_dir, 'cache'),
                os.path.join(self.data_dir, 'models'),
                os.path.join(self.data_dir, 'logs'),
                os.path.join(self.data_dir, 'backups')
            ]
            
            for directory in directories:
                os.makedirs(directory, exist_ok=True)
                logger.info(f"✅ {directory}")
            
            # Create configuration file
            config_path = os.path.join(self.data_dir, 'enterprise_config.json')
            if not os.path.exists(config_path):
                config = {
                    "engine": {
                        "type": "adaptive_hybrid",
                        "enable_graph": True,
                        "enable_embeddings": True,
                        "cache_size": 1000
                    },
                    "graph": {
                        "min_attribute_frequency": 2,
                        "enable_analytics": True,
                        "normalization_enabled": True
                    },
                    "embeddings": {
                        "embedding_dim": 128,
                        "hidden_dims": [256, 128],
                        "dropout_rate": 0.2,
                        "learning_rate": 0.001,
                        "epochs": 50,  # Reduced for setup
                        "batch_size": 16,
                        "validation_split": 0.2,
                        "early_stopping_patience": 10,
                        "margin": 1.0
                    },
                    "dataset": {
                        "wikidata_endpoint": "https://query.wikidata.org/sparql",
                        "request_timeout": 30,
                        "max_retries": 3,
                        "batch_size": 50,  # Reduced for setup
                        "duplicate_threshold": 0.8,
                        "min_data_quality": 0.5
                    },
                    "monitoring": {
                        "enabled": True,
                        "resource_interval": 1.0,
                        "max_history": 1000,  # Reduced for setup
                        "alert_cpu_threshold": 80.0,
                        "alert_memory_threshold": 85.0,
                        "alert_response_threshold": 2.0
                    }
                }
                
                with open(config_path, 'w') as f:
                    json.dump(config, f, indent=2)
                
                logger.info(f"✅ Created configuration: {config_path}")
            
            self.results['data_directory'] = {'success': True}
            return True
            
        except Exception as e:
            logger.error(f"Data directory setup failed: {e}")
            self.results['data_directory'] = {'success': False, 'error': str(e)}
            return False
    
    def run_tests(self) -> bool:
        """Run comprehensive test suite"""
        logger.info("🧪 Running comprehensive tests...")
        
        try:
            test_results = run_comprehensive_tests(self.data_dir)
            
            self.results['tests'] = test_results
            
            if test_results['summary']['passed'] == test_results['summary']['total']:
                logger.info(f"✅ All tests passed: {test_results['summary']['passed']}/{test_results['summary']['total']}")
                return True
            else:
                logger.warning(f"⚠️ Some tests failed: {test_results['summary']['passed']}/{test_results['summary']['total']}")
                logger.info(test_results['report'])
                return False
                
        except Exception as e:
            logger.error(f"Test execution failed: {e}")
            self.results['tests'] = {'success': False, 'error': str(e)}
            return False
    
    def expand_dataset(self, target_size: int = 100) -> bool:
        """Expand dataset with pipeline"""
        logger.info(f"📈 Expanding dataset to {target_size} songs...")
        
        try:
            config = PipelineConfig(
                batch_size=25,  # Reduced for setup
                max_retries=2,
                request_timeout=20
            )
            
            pipeline = DatasetPipeline(self.data_dir, config)
            
            # Expand with popular genres
            popular_genres = ["pop", "rock", "electronic", "hip-hop"]
            
            result = pipeline.expand_dataset(
                target_size=target_size,
                genres=popular_genres,
                era_start=2000,
                era_end=2023
            )
            
            self.results['dataset_expansion'] = {
                'success': len(result.errors) == 0,
                'total_songs': result.total_found,
                'quality_score': result.quality_score,
                'processing_time': result.processing_time,
                'errors': result.errors
            }
            
            if len(result.errors) == 0:
                logger.info(f"✅ Dataset expanded to {result.total_found} songs")
                logger.info(f"   Quality score: {result.quality_score:.3f}")
                logger.info(f"   Processing time: {result.processing_time:.1f}s")
                return True
            else:
                logger.warning(f"⚠️ Dataset expansion completed with {len(result.errors)} errors")
                for error in result.errors[:3]:
                    logger.warning(f"   - {error}")
                return len(result.errors) < 5  # Allow some errors
                
        except Exception as e:
            logger.error(f"Dataset expansion failed: {e}")
            self.results['dataset_expansion'] = {'success': False, 'error': str(e)}
            return False
    
    def train_embeddings(self) -> bool:
        """Train neural embeddings"""
        logger.info("🧠 Training neural embeddings...")
        
        try:
            # Check if PyTorch is available
            try:
                import torch
            except ImportError:
                logger.warning("⚠️ PyTorch not available, skipping embedding training")
                self.results['embeddings'] = {'success': False, 'reason': 'PyTorch not available'}
                return False
            
            from backend.logic.enterprise_embeddings import EnterpriseEmbeddingTrainer, EmbeddingConfig
            from backend.logic.kg_loader import load_dataset
            
            # Load dataset
            songs = load_dataset()
            if len(songs) < 10:
                logger.warning("⚠️ Insufficient songs for embedding training")
                self.results['embeddings'] = {'success': False, 'reason': 'Insufficient data'}
                return False
            
            # Create trainer with reduced epochs for setup
            config = EmbeddingConfig(
                embedding_dim=64,  # Reduced for setup
                epochs=10,  # Reduced for setup
                batch_size=8,
                validation_split=0.3
            )
            
            trainer = EnterpriseEmbeddingTrainer(config)
            
            # Train
            start_time = time.time()
            metrics = trainer.train(songs)
            training_time = time.time() - start_time
            
            # Save model
            model_path = os.path.join(self.data_dir, 'models', 'enterprise_embeddings.pt')
            trainer.save_model(model_path)
            
            # Evaluate
            evaluation = trainer.evaluate_embeddings(songs)
            
            self.results['embeddings'] = {
                'success': True,
                'training_loss': metrics.train_loss,
                'validation_loss': metrics.val_loss,
                'training_time': training_time,
                'evaluation': evaluation,
                'model_path': model_path
            }
            
            logger.info(f"✅ Embeddings trained successfully")
            logger.info(f"   Training loss: {metrics.train_loss:.4f}")
            logger.info(f"   Validation loss: {metrics.val_loss:.4f}")
            logger.info(f"   Training time: {training_time:.1f}s")
            
            if evaluation.get('f1_score'):
                logger.info(f"   F1 Score: {evaluation['f1_score']:.3f}")
            
            return True
            
        except Exception as e:
            logger.error(f"Embedding training failed: {e}")
            self.results['embeddings'] = {'success': False, 'error': str(e)}
            return False
    
    def initialize_system(self) -> bool:
        """Initialize enterprise system"""
        logger.info("🚀 Initializing enterprise system...")
        
        try:
            from backend.logic.adaptive_hybrid_engine import AdaptiveHybridEngine
            
            # Create engine
            engine = AdaptiveHybridEngine(
                data_dir=self.data_dir,
                enable_graph=True,
                enable_embeddings=True  # Will be disabled if not available
            )
            
            # Initialize
            success = engine.initialize()
            
            if success:
                # Get system status
                status = engine.get_system_status()
                
                self.results['system_initialization'] = {
                    'success': True,
                    'status': status
                }
                
                logger.info("✅ Enterprise system initialized successfully")
                logger.info(f"   Total songs: {status.get('total_songs', 0)}")
                logger.info(f"   Graph available: {status.get('graph_available', False)}")
                logger.info(f"   Embeddings available: {status.get('embeddings_available', False)}")
                
                return True
            else:
                logger.error("❌ System initialization failed")
                self.results['system_initialization'] = {'success': False}
                return False
                
        except Exception as e:
            logger.error(f"System initialization failed: {e}")
            self.results['system_initialization'] = {'success': False, 'error': str(e)}
            return False
    
    def verify_setup(self) -> bool:
        """Verify complete setup"""
        logger.info("🔍 Verifying complete setup...")
        
        try:
            # Check all components
            verification_results = {}
            
            # Check data files
            songs_path = os.path.join(self.data_dir, 'songs_kg.json')
            verification_results['data_files'] = os.path.exists(songs_path)
            
            # Check configuration
            config_path = os.path.join(self.data_dir, 'enterprise_config.json')
            verification_results['config'] = os.path.exists(config_path)
            
            # Check models
            model_path = os.path.join(self.data_dir, 'models', 'enterprise_embeddings.pt')
            verification_results['embeddings'] = os.path.exists(model_path)
            
            # Check system initialization
            try:
                from backend.logic.adaptive_hybrid_engine import AdaptiveHybridEngine
                engine = AdaptiveHybridEngine(self.data_dir)
                engine.initialize()
                verification_results['engine'] = True
            except:
                verification_results['engine'] = False
            
            # Overall verification
            all_good = all(verification_results.values())
            
            self.results['verification'] = {
                'success': all_good,
                'details': verification_results
            }
            
            if all_good:
                logger.info("✅ Setup verification passed")
            else:
                logger.warning("⚠️ Setup verification completed with issues")
                for component, status in verification_results.items():
                    status_str = "✅" if status else "❌"
                    logger.warning(f"   {status_str} {component}")
            
            return all_good
            
        except Exception as e:
            logger.error(f"Setup verification failed: {e}")
            self.results['verification'] = {'success': False, 'error': str(e)}
            return False
    
    def run_full_setup(self, target_size: int = 100, skip_tests: bool = False, 
                      skip_embeddings: bool = False) -> Dict[str, Any]:
        """Run complete enterprise setup"""
        logger.info("🎯 Starting full enterprise setup...")
        
        setup_start = time.time()
        
        # Setup steps
        steps = [
            ("Dependencies", self.check_dependencies),
            ("Data Directory", self.setup_data_directory),
        ]
        
        if not skip_tests:
            steps.append(("Tests", self.run_tests))
        
        steps.extend([
            ("Dataset Expansion", lambda: self.expand_dataset(target_size)),
        ])
        
        if not skip_embeddings:
            steps.append(("Embeddings", self.train_embeddings))
        
        steps.extend([
            ("System Initialization", self.initialize_system),
            ("Verification", self.verify_setup)
        ])
        
        # Execute steps
        for step_name, step_func in steps:
            logger.info(f"\n{'='*50}")
            logger.info(f"Step: {step_name}")
            logger.info(f"{'='*50}")
            
            try:
                success = step_func()
                if not success:
                    logger.warning(f"Step '{step_name}' completed with issues")
            except Exception as e:
                logger.error(f"Step '{step_name}' failed: {e}")
        
        total_time = time.time() - setup_start
        
        # Generate summary
        summary = {
            'setup_time': total_time,
            'steps_completed': len(steps),
            'results': self.results,
            'success': all(
                result.get('success', False) 
                for result in self.results.values() 
                if isinstance(result, dict)
            )
        }
        
        # Print final summary
        logger.info(f"\n{'='*50}")
        logger.info("🎉 ENTERPRISE SETUP COMPLETE")
        logger.info(f"{'='*50}")
        logger.info(f"Total time: {total_time:.1f}s")
        logger.info(f"Overall success: {summary['success']}")
        
        if summary['success']:
            logger.info("\n✅ Your enterprise Music Akenator is ready!")
            logger.info("\nNext steps:")
            logger.info("1. Start backend: python app.py")
            logger.info("2. Start frontend: cd song-genie-ui && npm run dev")
            logger.info("3. Visit: http://localhost:3000")
        else:
            logger.info("\n⚠️ Setup completed with some issues")
            logger.info("Check the logs above for details")
        
        return summary


def main():
    """Main setup function"""
    parser = argparse.ArgumentParser(description="Enterprise Music Akenator Setup")
    parser.add_argument("--data-dir", help="Data directory path")
    parser.add_argument("--target-size", type=int, default=100, help="Target dataset size")
    parser.add_argument("--skip-tests", action="store_true", help="Skip comprehensive tests")
    parser.add_argument("--skip-embeddings", action="store_true", help="Skip embedding training")
    parser.add_argument("--verify-only", action="store_true", help="Only verify existing setup")
    parser.add_argument("--quick", action="store_true", help="Quick setup (minimal testing)")
    
    args = parser.parse_args()
    
    # Create setup instance
    setup = EnterpriseSetup(args.data_dir)
    
    if args.verify_only:
        # Only verify existing setup
        success = setup.verify_setup()
        sys.exit(0 if success else 1)
    elif args.quick:
        # Quick setup
        summary = setup.run_full_setup(
            target_size=50,
            skip_tests=False,
            skip_embeddings=True
        )
    else:
        # Full setup
        summary = setup.run_full_setup(
            target_size=args.target_size,
            skip_tests=args.skip_tests,
            skip_embeddings=args.skip_embeddings
        )
    
    # Save results
    results_path = os.path.join(setup.data_dir, 'setup_results.json')
    with open(results_path, 'w') as f:
        json.dump(summary, f, indent=2, default=str)
    
    logger.info(f"\n📄 Setup results saved to: {results_path}")
    
    sys.exit(0 if summary['success'] else 1)


if __name__ == "__main__":
    main()
