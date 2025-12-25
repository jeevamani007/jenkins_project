# Port Conflict Solutions

## Problem
Your testing project and testing tool both want to use port 8000, causing conflicts.

## Solutions

### Solution 1: Use Different Port (Recommended)
```bash
# Windows
set PORT=8001 && python app.py

# Linux/Mac
PORT=8001 python app.py
```

### Solution 2: Auto-Detect Available Port
The app automatically finds an available port (8000-8009) if the default is taken.

### Solution 3: Use Start Scripts

**Windows:**
```bash
start.bat
```

**Linux/Mac:**
```bash
chmod +x start.sh
./start.sh
```

### Solution 4: Check What's Using the Port

**Windows:**
```bash
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

**Linux/Mac:**
```bash
lsof -i :8000
kill -9 <PID>
```

### Solution 5: Use Different Ports for Each Project

**Testing Project:**
```bash
PORT=8000 python app.py
```

**Testing Tool:**
```bash
PORT=8001 python app.py
```

## Recommended Setup

1. **Testing Project**: Port 8000
2. **Testing Tool Dashboard**: Port 8001

Set in environment or use:
```bash
# Testing Tool
PORT=8001 python app.py
```

## Environment Variables

You can set these before running:
- `PORT` - Server port (default: 8000)
- `HOST` - Server host (default: 0.0.0.0)
- `AUTO_RELOAD` - Auto-reload on changes (default: true)

Example:
```bash
PORT=8001 HOST=127.0.0.1 AUTO_RELOAD=false python app.py
```





