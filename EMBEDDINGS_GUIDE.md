# 🧠 Neural Embeddings Guide

## 🔄 Current System vs Embeddings

### 📊 Current Tag-Based System
- **Fixed categories**: "Is it pop?" "Is it by Lady Gaga?"
- **Binary logic**: Songs either have a tag or don't
- **No nuance**: Can't understand that "electropop" ≈ "dance-pop"
- **Manual rules**: Questions based on predefined attributes

### 🧠 Neural Embedding System
- **Learned understanding**: Neural network discovers relationships automatically
- **Vector similarity**: Songs represented as 128-dimensional vectors
- **Semantic nuance**: Understands degrees of similarity
- **Automatic discovery**: Finds patterns humans might miss

## 🎯 How Embeddings Work

### 1. **Representation Learning**
```python
song_metadata = {
    "genres": ["pop", "dance"],
    "artist": "Lady Gaga",
    "era": "2000s",
    "duration": 216
}

# Neural network converts to:
song_embedding = [0.2, -0.8, 0.1, 0.9, ...]  # 128 numbers
```

### 2. **Similarity Calculation**
```python
# Instead of counting matching tags:
similarity = cosine_similarity(embedding1, embedding2)
# Result: 0.73 (73% similar)
```

### 3. **Smart Questions**
Questions generated based on what separates songs in vector space:
- "Is it upbeat?" (learned from audio patterns)
- "Is it a female solo artist?" (discovered automatically)
- "Is it from the 2000s?" (temporal patterns)

## 🚀 Getting Started

### 1. Install Dependencies
```bash
cd song-genie
pip install -r requirements.txt
```

### 2. Train Embeddings
```bash
python train_embeddings.py
```
This will:
- Load your song dataset
- Train a neural network for ~5 minutes
- Save the model to `backend/data/song_embeddings.pt`
- Show example similarities

### 3. Enable Embeddings in Game
Start the game with embeddings:
```bash
# Frontend: http://localhost:3000?embeddings=true
# Or call API: GET /start?embeddings=true
```

## 🔧 Technical Details

### **Neural Architecture**
```
Metadata Features → Encoder Network → 128D Embedding
                    (256 → 128 → 128)
```

### **Training Process**
1. **Positive pairs**: Same genre, era, or artist
2. **Negative pairs**: Different songs
3. **Contrastive loss**: Pull similar together, push different apart
4. **100 epochs**: ~5 minutes training time

### **Feature Encoding**
- **Genres**: One-hot encoded
- **Artists**: Top 100 artists + unknown
- **Numerical**: Year, duration, BPM (normalized)
- **Binary**: Awards, soundtrack, collaboration

## 🎮 Benefits

### **Better Questions**
- **Semantic**: "Is it danceable?" vs "Is it dance-pop?"
- **Nuanced**: Understands relationships between genres
- **Adaptive**: Questions based on actual song patterns

### **Improved Guessing**
- **Contextual**: Understands song context, not just tags
- **Flexible**: Can handle new genre combinations
- **Accurate**: Vector similarity > tag matching

### **Smart Learning**
- **Pattern recognition**: Discovers what makes songs similar
- **Continuous**: Improves with more songs
- **Explainable**: Can show why songs are similar

## 📊 Example Results

After training, you'll see:
```
LoveGame is similar to:
  - Poker Face (0.89) - Same artist, similar style
  - Bad Romance (0.85) - Dance-pop, female artist
  - Just Dance (0.82) - Same era, upbeat tempo
```

## 🔄 Comparison Summary

| Feature | Tag-Based | Embeddings |
|---------|------------|------------|
| **Questions** | Fixed categories | Learned patterns |
| **Similarity** | Count matching tags | Vector cosine similarity |
| **Nuance** | Binary (yes/no) | Continuous (0-1) |
| **Discovery** | Manual rules | Automatic learning |
| **Adaptability** | Static | Improves with data |
| **Setup** | Instant | 5-minute training |

## 🛠️ Advanced Usage

### **Custom Questions**
The system learns question types automatically:
- Genre clusters → "Is it electronic music?"
- Era patterns → "Is it a 2000s hit?"
- Artist styles → "Is it experimental?"

### **Similarity API**
```bash
# Find similar songs
GET /similar?song=LoveGame&top_k=5

# Explain similarity
GET /explain?song1=LoveGame&song2=PokerFace
```

### **Hybrid Mode**
Can combine tag-based and embedding questions for best results.

## 🔍 Troubleshooting

### **PyTorch Installation**
```bash
# CPU version (faster install)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# GPU version (if you have NVIDIA)
pip install torch torchvision torchaudio
```

### **Training Issues**
- **Not enough songs**: Need at least 10 songs
- **Poor data quality**: Ensure metadata is complete
- **Memory issues**: Reduce batch size in training script

### **Embedding Quality**
- **Low similarity**: Check data quality
- **Weird results**: May need more training epochs
- **No patterns**: Dataset too diverse

## 🎯 Future Enhancements

1. **Audio Features**: Add MFCC, spectral analysis
2. **Lyrics Embeddings**: NLP-based text understanding
3. **User Feedback**: Learn from game performance
4. **Genre Evolution**: Track changes over time
5. **Cross-modal**: Combine audio + metadata + lyrics

---

**Ready to upgrade your Music Akenator to neural intelligence? 🚀**
