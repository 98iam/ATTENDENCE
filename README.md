# 📚 Attendance System

A modern, interactive web-based attendance system built with Flask. Features an intuitive swipe interface for quick attendance marking with real-time statistics and data export capabilities.

## ✨ Features

- **Interactive Swipe Interface**: Tinder-like card swipe functionality for quick attendance marking
- **Real-time Statistics**: Live updates of present/absent counts
- **Modern UI**: Clean, responsive design with smooth animations
- **Export Functionality**: Download attendance data as CSV
- **Touch & Mouse Support**: Works on both desktop and mobile devices
- **Keyboard Shortcuts**: Use arrow keys or P/A keys for quick marking

## 🚀 Quick Start

### Prerequisites
- Python 3.7+
- Flask

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/attendance-system.git
cd attendance-system
```

2. Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install flask
```

4. Run the application:
```bash
python3 run.py
```

5. Open your browser and navigate to `http://localhost:5000`

## 🎯 How to Use

1. **Dashboard**: View total students and current attendance statistics
2. **Start Attendance**: Click "Start Attendance" to begin the marking process
3. **Mark Attendance**: 
   - Swipe up or press ↑/P for Present
   - Swipe down or press ↓/A for Absent
   - Use mouse drag on desktop
4. **View Results**: Check attendance summary and export data

## 🏗️ Project Structure

```
attendance-system/
├── app/
│   ├── __init__.py          # Flask app initialization
│   ├── routes.py            # Application routes and logic
│   ├── templates/
│   │   ├── attendance.html  # Main attendance interface
│   │   └── index.html       # Basic template
│   └── static/
│       └── css/
├── run.py                   # Application entry point
├── README.md
└── .gitignore
```

## 🎨 Features Overview

### Dashboard
- Student count display
- Real-time attendance statistics
- Date display
- Quick action buttons

### Attendance Mode
- Card-based student interface
- Smooth swipe animations
- Progress tracking
- Visual feedback for marking

### Results Page
- Present/absent student lists
- Summary statistics
- CSV export functionality
- Navigation controls

## 🛠️ Customization

### Adding Students
Modify the `students_data` list in `app/routes.py`:

```python
students_data = [
    {'roll_number': '001', 'name': 'Student Name'},
    # Add more students here
]
```

### Database Integration
Currently uses in-memory storage. To integrate with a database:

1. Install your preferred database library (SQLAlchemy, etc.)
2. Replace the `attendance_records` dictionary with database operations
3. Update the routes to use database queries

## 🔧 API Endpoints

- `GET /attendance` - Main attendance interface
- `POST /mark_attendance` - Mark student attendance
- `GET /get_attendance/<date>` - Retrieve attendance for specific date
- `GET /export_attendance/<date>` - Export attendance data
- `GET /students` - Get all students
- `POST /add_student` - Add new student

## 📱 Mobile Support

The application is fully responsive and supports touch gestures:
- Touch and drag to mark attendance
- Optimized layouts for mobile devices
- Fast, smooth animations

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🎯 Future Enhancements

- [ ] Database integration (SQLite/PostgreSQL)
- [ ] User authentication and authorization
- [ ] Multiple class support
- [ ] Attendance reports and analytics
- [ ] Email notifications
- [ ] Backup and restore functionality
- [ ] Dark mode support

## 📞 Support

If you encounter any issues or have questions, please:
1. Check the existing issues
2. Create a new issue with detailed description
3. Include steps to reproduce the problem

---

Made with ❤️ using Flask and modern web technologies.