# 🚀 Music Akenator - Startup Guide

## ✅ YOUR SYSTEM IS WORKING!

The connection test shows:
- ✅ **Core System**: 71 songs, 121 questions
- ✅ **Backend**: All endpoints working
- ✅ **Health Check**: Responding correctly

---

## 🎯 HOW TO START YOUR APP

### **Step 1: Start Backend (Terminal 1)**
```bash
cd "c:\Users\RG Saran Vishakan\Desktop\Music-Akenator\song-genie"
python app.py
```

You should see:
```
🚀 Starting Enhanced Music Akenator Flask App...
🌐 Server: http://127.0.0.1:5000
🎵 Using your verified enhanced system!
* Running on http://127.0.0.1:5000
```

### **Step 2: Start Frontend (Terminal 2)**
```bash
cd "c:\Users\RG Saran Vishakan\Desktop\Music-Akenator\song-genie-ui"
npm run dev
```

You should see:
```
▲ Next.js 16.1.6 (Turbopack)
- Local: http://localhost:3000
✓ Ready in 2.1s
```

### **Step 3: Use Your App**
Open browser: **http://localhost:3000**

---

## 🔍 TROUBLESHOOTING

### **If you see "backend unreachable":**

1. **Check if backend is running**:
   - Visit: http://127.0.0.1:5000/health
   - Should see: `{"status": "ok", "service": "Music Akenator Enhanced System"}`

2. **Check if frontend is running**:
   - Visit: http://localhost:3000
   - Should see the Song Genie interface

3. **Both must be running in separate terminals!**

### **Common Issues:**

#### **Backend Issues:**
- **Error**: `ModuleNotFoundError`
- **Fix**: Make sure you're in `song-genie` directory
- **Fix**: Install dependencies: `pip install flask flask-cors`

#### **Frontend Issues:**
- **Error**: `npm command not found`
- **Fix**: Install Node.js from https://nodejs.org
- **Fix**: Run in `song-genie-ui` directory

#### **Connection Issues:**
- **Error**: "backend unreachable"
- **Fix**: Make sure BOTH servers are running
- **Fix**: Check firewall isn't blocking port 5000

---

## 🎮 TESTING YOUR APP

### **Quick Test:**
1. **Backend Health**: http://127.0.0.1:5000/health
2. **Frontend**: http://localhost:3000
3. **Game Page**: http://localhost:3000/game

### **What Should Happen:**
1. Click "Start Game"
2. See first question
3. Answer questions
4. Get song guess
5. Play song option

---

## 📊 YOUR SYSTEM FEATURES

### **✅ Working Features:**
- **71 Songs**: Your verified dataset
- **121 Questions**: Intelligent question generation
- **Graph Reasoning**: Knowledge graph system
- **Confidence**: Smart guessing algorithm
- **CORS**: Frontend-backend communication
- **Sessions**: Game state management

### **🎵 Game Flow:**
1. Start new session
2. Ask intelligent questions
3. Update beliefs based on answers
4. Make confident guess
5. Show top 3 candidates
6. Play song option

---

## 🚀 ALTERNATIVE STARTUP

### **If you want to test quickly:**
```bash
# Test backend only
python test_connection.py

# Start both servers (if you have the script)
python run_both.py  # if available
```

---

## 🎯 SUCCESS INDICATORS

### **✅ Everything Working When:**
- Backend shows: `* Running on http://127.0.0.1:5000`
- Frontend shows: `✓ Ready in Xs`
- Health check: `{"status": "ok"}`
- Game starts without errors
- Questions appear correctly

### **❌ Issues When:**
- "backend unreachable" error
- Red error messages in terminals
- Health check fails
- Game doesn't start

---

## 💡 PRO TIPS

1. **Keep both terminals open** while playing
2. **Don't close terminals** - it stops the servers
3. **Use Ctrl+C** to stop servers gracefully
4. **Refresh browser** if something seems stuck
5. **Check terminal logs** for error messages

---

**🎉 Your Music Akenator is ready to use!**

Just follow the 3 steps above and enjoy your enhanced music guessing game! 🎵
