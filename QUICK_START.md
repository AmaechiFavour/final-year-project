# Quick Start Guide - E-Learning Portal

## 🚀 Get Running in 5 Minutes

### Windows Quick Start

**Option 1: Double-click (Easiest)**
1. Create a file called `run.bat` in the project folder with this content:
```batch
@echo off
cd /d "%~dp0"
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)
call venv\Scripts\activate.bat
pip install -r requirements.txt
python init_db.py
python main_enhanced.py
```

2. Double-click `run.bat` and wait for "Running on http://localhost:5000"

**Option 2: Command Prompt**
```batch
# Navigate to project folder
cd path\to\E-Learning-Portal-using-Flask-main

# Create virtual environment (first time only)
python -m venv venv

# Activate virtual environment
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Initialize database (first time only)
python init_db.py

# Run application
python main_enhanced.py
```

### Mac/Linux Quick Start

```bash
# Navigate to project folder
cd path/to/E-Learning-Portal-using-Flask-main

# Create virtual environment (first time only)
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies (first time only)
pip install -r requirements.txt

# Initialize database (first time only)
python init_db.py

# Run application
python main_enhanced.py
```

## ✅ What to Expect

After running the app, you should see:

```
 * Running on http://127.0.0.1:5000
 * Press CTRL+C to quit
```

## 🌐 Access the Application

1. Open your web browser
2. Go to: **http://localhost:5000**
3. You should see the home page

## 🔐 First Login

**Admin Login** (to see all features):
- Email: `admin@elearning.local`
- Password: `admin123`

**Teacher Login** (to create content):
- Email: `john.smith@faculty.local`
- Password: `teacher123`

**Student Login** (to take courses):
- Email: `student1@faculty.local`
- Password: `student123`

## 📁 Where are my files?

- **Database**: `elearning.db` (in project folder)
- **Uploaded files**: `uploads/` (in project folder)
- **Application code**: `main_enhanced.py`

## 🛑 Stop the Application

Press `CTRL+C` in the terminal/command prompt

## 🔄 Next Time

If app was working before, just run:
```bash
python main_enhanced.py
```
(No need to reinstall or reinitialize)

## ⚠️ Common Issues

### "ModuleNotFoundError"
- Make sure virtual environment is activated
- Run: `pip install -r requirements.txt`

### "Address already in use"
- Another app is using port 5000
- Close other Flask apps or change port in code

### "Database locked"
- Close the application
- Delete `elearning.db`
- Run: `python init_db.py`

## 📖 Learn More

See `README.md` for comprehensive documentation.

---

**Enjoy your E-Learning Portal! 🎓**
