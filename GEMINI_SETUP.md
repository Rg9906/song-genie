# 🤖 Gemini API Setup Guide

## 🏆 **Why Gemini API is Better Than Ollama**

### **✅ Gemini API Advantages**
- **No installation needed** - Just API key
- **Better quality** - Google's advanced model
- **Faster** - Cloud-based processing
- **Reliable** - Google's infrastructure
- **Free tier** - 60 requests/minute
- **Perfect for** - Creative question generation

### **❌ Ollama Disadvantages**
- **Local setup required** - Installation + model downloads
- **Memory intensive** - 2-8GB RAM needed
- **Slower** - Local processing
- **Model limitations** - Smaller models like phi3

---

## 🚀 **Quick Setup (5 Minutes)**

### **Step 1: Get Gemini API Key (Free)**
1. Go to https://makersuite.google.com/app/apikey
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy your API key (looks like: `AIzaSy...`)

### **Step 2: Add API Key to Your System**

**Option A: Environment Variable (Recommended)**
```bash
# Windows (PowerShell)
$env:GEMINI_API_KEY = "your_api_key_here"

# Or add to system environment variables permanently
```

**Option B: Directly in Code**
```python
# In backend/logic/gemini_service.py, change line 11:
self.api_key = "your_api_key_here"  # Replace with your key
```

### **Step 3: Test Your Setup**
```bash
python test_ultimate_system.py
```

You should see: `🤖 Using gemini for AI generation`

---

## 🎯 **What Gemini Will Generate**

### **Creative Questions You'll See:**
- "Would this get you dancing at a party?"
- "Does this sound like a late-night drive song?"
- "Is this more of a feel-good summer vibe?"
- "Would you hear this at a coffee shop?"
- "Does this make you feel nostalgic?"

### **vs Current Template Questions:**
- "Could this be described as Olivia Rodrigo?"
- "Does this have elements of Nelly Furtado?"

---

## 📊 **Gemini vs Current System**

### **Before (Current Templates)**:
- Fixed templates: "Could this be described as {artist}?"
- Limited to your existing attributes
- Repetitive patterns
- No creativity

### **After (Gemini AI)**:
- ✅ **Creative questions**: AI generates unique questions
- ✅ **Natural phrasing**: Conversational and engaging
- ✅ **Dynamic variety**: Never asks the same question twice
- ✅ **Context-aware**: Uses your song data for inspiration
- ✅ **Human-like**: Sounds like a real music expert

---

## 🔧 **Advanced Configuration**

### **Customize Gemini Prompts**
In `backend/logic/gemini_service.py`, you can edit the prompt:

```python
prompt = f"""You are a friendly music guessing game host...
# Add your custom instructions here
Generate questions that are:
- More emotional
- About specific moods
- About time periods
- About dance styles
"""
```

### **Adjust Creativity**
```python
"generationConfig": {
    "temperature": 0.9,    # Higher = more creative (0.0-1.0)
    "topK": 40,           # Variety of responses
    "maxOutputTokens": 50  # Max question length
}
```

---

## 🎮 **Test Gemini Integration**

### **Run This Test**:
```python
python -c "
from backend.logic.free_ai_integrator import FreeAIIntegrator
ai = FreeAIIntegrator()
print('Status:', ai.active_service.__class__.__name__ if ai.active_service else 'None')
"
```

### **Expected Output**:
```
🤖 Using gemini for AI generation
Status: GeminiService
```

---

## 🚨 **Troubleshooting**

### **"No AI services available"**
- Check your API key is correct
- Make sure you have internet connection
- Verify Gemini API is enabled

### **"API key not found"**
- Set environment variable correctly
- Check spelling of `GEMINI_API_KEY`
- Try restarting your terminal

### **Rate Limits**
- Free tier: 60 requests/minute
- If you hit limits, wait a minute and retry
- For production, consider paid tier

---

## 💰 **Cost**

### **Free Tier (What You Have)**:
- ✅ **60 requests/minute**
- ✅ **15 requests/minute sustained**
- ✅ **Unlimited questions per day**
- ✅ **No credit card needed**

### **Paid Tier (If Needed)**:
- **$0.00025 per 1,000 characters** (very cheap)
- **Higher rate limits**
- **More models available**

---

## 🎉 **You're Ready!**

Once you set up your API key, your Music Akenator will:

1. **Generate creative questions** using Gemini AI
2. **Never repeat questions** - always fresh
3. **Sound natural** - like a real music expert
4. **Adapt to your data** - uses your songs as inspiration
5. **Engage users** - fun, conversational questions

**This is a massive upgrade from template-based questions!** 🚀

---

## 🔄 **Switch Back to Ollama (If You Want)**

If you prefer local AI, you can still use Ollama:
1. Install Ollama
2. Download model
3. Gemini will be used first, Ollama as fallback

**But Gemini is recommended for better quality and easier setup!** ✨
