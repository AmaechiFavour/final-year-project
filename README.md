# 🎓 E-Learning Portal for Faculty of Computing

A comprehensive, fully offline, feature-rich Learning Management System (LMS) built with Flask. Similar to Frappe LMS but designed as a standalone, desktop-friendly application with no Docker or external dependencies.

## ✨ Features

### 🎯 Core Features
- **User Management**: Admin, Teacher, and Student roles with granular permissions
- **Course Management**: Create, edit, publish, and manage courses with full control
- **Lessons & Content**: Rich text lessons with video and resource support
- **Quizzes**: Multiple-choice, true/false, and short-answer questions with auto-grading
- **Assignments**: Submit assignments with file upload support and teacher grading
- **Progress Tracking**: Automatic progress tracking for students per course
- **Enrollments**: Students can browse and enroll in courses
- **Announcements**: Teachers can post course announcements
- **Student Dashboard**: View enrolled courses, track progress, and access learning materials
- **Teacher Dashboard**: Manage courses, view student progress, and grade assignments
- **Admin Dashboard**: Manage users, courses, and system settings

### 🔧 Technical Features
- **Fully Offline**: No internet required, works completely local
- **SQLite Database**: Lightweight, file-based database
- **File Upload Support**: Upload videos, documents, and assignment submissions (up to 500MB)
- **Responsive Design**: Works on desktop and tablet
- **Role-Based Access Control**: Admin, Teacher, Student roles
- **Data Persistence**: All data stored locally in SQLite database

## 📋 System Requirements

- **Python 3.8+**
- **Windows, Mac, or Linux**
- **Minimum 2GB RAM**
- **500MB disk space (plus space for course videos/content)**

## 🚀 Installation & Setup

### Windows One-Click Client Setup (Recommended)

1. Open the project folder.
2. Double-click `install.bat` and wait for setup to finish.
3. After setup completes, run `start.bat` anytime you want to launch the app.

`run.bat` is also available as a one-click setup + start wrapper.

### Step 1: Install Python
Download and install Python 3.8+ from [python.org](https://www.python.org/)
Make sure to check "Add Python to PATH" during installation.

### Step 2: Clone or Extract Project
Extract the project to your desired location:
```bash
cd E-Learning-Portal-using-Flask-main
```

### Step 3: Create Virtual Environment (Recommended)
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Mac/Linux
python3 -m venv venv
source venv/bin/activate
```

### Step 4: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 5: Initialize Database with Sample Data
```bash
python init_db.py
```

This will:
- Create all database tables
- Add sample users (admin, teachers, students)
- Add sample courses with lessons, quizzes, and assignments
- Display test credentials on screen

### Step 6: Run the Application
```bash
python main_enhanced.py
```

The application will start at: **http://localhost:5000**

## 🔐 Test Credentials

After initialization, you can log in with:

### Admin Account
- **Email**: admin@elearning.local
- **Password**: admin123
- **Access**: Full system administration

### Teacher Account
- **Email**: john.smith@faculty.local
- **Password**: teacher123
- **Access**: Create and manage courses

### Student Account
- **Email**: student1@faculty.local (student2, student3, ... student10)
- **Password**: student123
- **Access**: Browse and enroll in courses

## 📁 Project Structure

```
E-Learning-Portal-using-Flask-main/
├── main_enhanced.py              # Main Flask application
├── models.py                      # Database models
├── init_db.py                     # Database initialization script
├── requirements.txt               # Python dependencies
├── .env                          # Environment configuration
├── uploads/                      # Uploaded files storage
├── templates/                    # HTML templates
│   ├── base.html                # Base template
│   ├── index.html               # Home page
│   ├── login.html               # Login page
│   ├── register.html            # Registration page
│   ├── student_dashboard.html   # Student dashboard
│   ├── teacher_dashboard.html   # Teacher dashboard
│   ├── admin_dashboard.html     # Admin dashboard
│   ├── course_detail.html       # Course details
│   ├── lesson.html              # View lesson
│   ├── quiz_start.html          # Quiz start page
│   ├── quiz_question.html       # Quiz questions
│   ├── assignment.html          # Assignment page
│   └── ...
└── static/                       # CSS, JavaScript, images
    └── css/
        └── style.css
```

## 🎮 Usage Guide

### For Students

1. **Register/Login**: Create account or login as student
2. **Browse Courses**: Visit "Browse Courses" to see available courses
3. **Enroll**: Click "Enroll" to join a course
4. **Learn**: Access lessons, watch videos, read materials
5. **Complete**: Mark lessons as complete as you progress
6. **Quiz**: Take quizzes to test knowledge (scores auto-calculated)
7. **Assignments**: Submit assignments with text or file uploads
8. **Track Progress**: View your progress percentage in dashboard

### For Teachers

1. **Login**: Login with teacher credentials
2. **Create Course**: Go to "Create Course" in teacher dashboard
3. **Add Content**: Add lessons with text, HTML, and videos
4. **Create Quizzes**: Add quizzes with questions and options (auto-grading)
5. **Create Assignments**: Create assignments for students
6. **Manage Students**: View enrolled students and their progress
7. **Grade**: Grade student assignments and provide feedback
8. **View Progress**: See real-time student progress tracking

### For Administrators

1. **Login**: Login with admin credentials
2. **Manage Users**: Create, edit, or delete users
3. **Manage Courses**: View, publish, or delete courses
4. **View Statistics**: See system-wide usage statistics
5. **Course Management**: Archive or manage courses

## 🎬 Video Upload

Teachers can upload course videos. Supported formats:
- MP4, AVI, MOV (recommended: MP4)
- Maximum size: 500MB per file
- Videos are stored in `uploads/` folder

## 📝 Customization

### Change Application Name
Edit `main_enhanced.py`:
```python
app.config['SITE_NAME'] = 'Your Institution Name'
```

### Change Port
Edit `main_enhanced.py` at the end:
```python
app.run(debug=True, host='0.0.0.0', port=8000)  # Change 5000 to desired port
```

### Change Database
Edit `main_enhanced.py`:
```python
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///your_database_name.db'
```

## 🔒 Security Notes

⚠️ **IMPORTANT**: This is designed for **offline, educational use only**.

For production use, you must:
1. Change the `SECRET_KEY` in `main_enhanced.py`
2. Use proper password hashing (werkzeug.security)
3. Add HTTPS/SSL certificates
4. Implement proper authentication middleware
5. Add rate limiting and CSRF protection
6. Regular database backups

## 🐛 Troubleshooting

### Issue: "Port 5000 already in use"
```bash
# Change port in main_enhanced.py or use:
python main_enhanced.py --port 8000
```

### Issue: "Module not found"
```bash
# Reinstall dependencies
pip install -r requirements.txt
```

### Issue: "Database locked"
```bash
# Stop the application and delete elearning.db
# Then reinitialize:
python init_db.py
```

### Issue: "Upload folder permissions"
```bash
# Create uploads folder manually
mkdir uploads
```

## 📈 Database Backup

Backup your data regularly:
```bash
# Copy the database file
copy elearning.db elearning_backup_$(date).db
```

## 🛠️ Development

### Add New Models
1. Edit `models.py` to add new database models
2. Update `main_enhanced.py` to add routes
3. Create corresponding HTML templates
4. Run `python init_db.py` to reinitialize database

### Modify Styling
- Edit `templates/base.html` for base styling
- Add custom CSS in `static/css/style.css`
- Uses Bootstrap 5 by default

## 📚 Next Steps - Online Features (Future)

The current version is fully functional offline. To add online features later:
1. Deploy to cloud server (AWS, Azure, Heroku)
2. Use PostgreSQL/MySQL instead of SQLite
3. Add real-time notifications
4. Implement video streaming
5. Add social features (forums, messaging)

## 📞 Support

For issues or questions:
1. Check troubleshooting section above
2. Review code comments in `main_enhanced.py`
3. Check database schema in `models.py`

## 📄 License

This project is created for educational purposes.

## 🙏 Credits

Inspired by Frappe LMS but built as a lightweight, standalone Flask application for offline educational use.

---

**Happy Learning! 🚀**

For your friend's project - Faculty of Computing E-Learning Portal
- Course Id

To run this project first create database, and add that in the SQL URI in main.py, create the tables mentioned, check the details and more specification on each attribute in
the models.py. Install all libraries within a virtual environment as mentioned in the main.py and then run it. Note: dont forget to change the config details in the app.py to get
the notifications on the mail.
