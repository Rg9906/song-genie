# 🔧 Music Akenator - Troubleshooting Guide

## ❌ "Backend Unreachable" Error - FIXED!

### **Problem**
You're getting "backend unreachable" when trying to run the program.

### **Root Cause**
The original `app.py` was using old system components that had import errors and missing dependencies.

### **✅ SOLUTION**

#### **Step 1: Use the Fixed App**
Run the fixed version instead of the original:

```bash
# Navigate to the song-genie directory
cd "c:\Users\RG Saran Vishakan\Desktop\Music-Akenator\song-genie"

# Run the fixed app
python start_fixed.py
```

#### **Step 2: Alternative - Run Fixed App Directly**
```bash
python app_fixed.py
```

#### **Step 3: Check if it's Working**
You should see:
```
🚀 Starting Music Akenator...
🌐 Using fixed app with verified components
🌐 Server: http://127.0.0.1:5000
✅ Ready to start!
```

---

## 🔍 Common Issues & Solutions

### **1. Import Errors**
**Error**: `ModuleNotFoundError: No module named 'backend'`

**Solution**: Make sure you're in the correct directory:
```bash
cd "c:\Users\RG Saran Vishakan\Desktop\Music-Akenator\song-genie"
```

### **2. Port Already in Use**
**Error**: `Address already in use`

**Solution**: Change the port in `backend/logic/config.py`:
```python
FLASK_PORT: int = int(os.getenv("SONG_GENIE_FLASK_PORT", "5001"))  # Change to 5001
```

### **3. CORS Issues**
**Error**: "CORS policy error"

**Solution**: The fixed app already has CORS enabled. Make sure you're using `app_fixed.py`.

### **4. Session Errors**
**Error**: "Invalid or expired session"

**Solution**: Start a new game session:
- Refresh the browser
- Or call `/start` endpoint again

---

## 🛠️ What Was Fixed

### **Original Issues**
1. **Import Errors**: Old app used missing components
2. **Broken Dependencies**: References to non-existent modules
3. **CORS Issues**: Missing proper CORS configuration
4. **Session Management**: Complex session logic causing errors

### **Fixed App Improvements**
1. ✅ **Verified Components**: Uses tested `simple_enhanced.py`
2. ✅ **Proper CORS**: Cross-origin requests enabled
3. ✅ **Error Handling**: Comprehensive error catching
4. ✅ **Simple Session**: Clean session management
5. ✅ **Health Checks**: `/status` and `/health` endpoints
6. ✅ **Logging**: Clear error messages and status

---

## 🚀 Quick Start Guide

### **Option 1: Use Startup Script (Recommended)**
```bash
cd "c:\Users\RG Saran Vishakan\Desktop\Music-Akenator\song-genie"
python start_fixed.py
```

### **Option 2: Run Directly**
```bash
cd "c:\Users\RG Saran Vishakan\Desktop\Music-Akenator\song-genie"
python app_fixed.py
```

### **Option 3: If You Have Flask Issues**
```bash
# Install Flask if needed
pip install flask flask-cors

# Then run
python start_fixed.py
```

---

## 🌐 Accessing the Application

Once running, open your browser to:
- **Main App**: http://127.0.0.1:5000
- **Health Check**: http://127.0.0.1:5000/health
- **System Status**: http://127.0.0.1:5000/status

---

## 📊 Testing the Fixed App

### **Test 1: Start a Game**
```bash
curl http://127.0.0.1:5000/start
```

### **Test 2: Check Health**
```bash
curl http://127.0.0.1:5000/health
```

### **Test 3: Check System Status**
```bash
curl http://127.0.0.1:5000/status
```

---

## 🔧 Debug Mode

To enable debug mode for better error messages:

1. **Edit Config**: In `backend/logic/config.py`:
```python
FLASK_DEBUG: bool = True
```

2. **Or Set Environment Variable**:
```bash
set SONG_GENIE_FLASK_DEBUG=true
python start_fixed.py
```

---

## 📋 Verification Checklist

- [ ] You're in the `song-genie` directory
- [ ] Using `app_fixed.py` or `start_fixed.py`
- [ ] Flask and Flask-CORS are installed
- [ ] Port 5000 is not blocked by firewall
- [ ] No Python import errors

---

## 🎯 Still Having Issues?

### **Check These Things**
1. **Python Version**: Python 3.7+ recommended
2. **Dependencies**: `pip install flask flask-cors`
3. **Directory**: Make sure you're in `song-genie` folder
4. **Permissions**: Run as administrator if needed

### **Get Help**
1. **Check Logs**: Look for error messages in the console
2. **Test Components**: Run `python -c "from backend.logic.simple_enhanced import create_simple_enhanced_akenator; print('OK')"`
3. **Verify Flask**: Run `python -c "import flask; print('Flask OK')"`

---

## 🎉 Success Indicators

You know it's working when you see:
```
🚀 Starting Music Akenator...
🌐 Using fixed app with verified components
🌐 Server: http://127.0.0.1:5000
✅ Ready to start!
 * Serving Flask app 'app_fixed'
 * Running on http://127.0.0.1:5000
```

And when you visit http://127.0.0.1:5000 in your browser, the Music Akenator interface loads!

---

**🎯 The "Backend Unreachable" error is now FIXED! Use the fixed app and enjoy playing Music Akenator!** 🎵
