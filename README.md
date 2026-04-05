# 🗳️ CoSSA Portal & Secure Voting Platform

A professional, high-performance web application built for the **Computer Science Students Association (CoSSA)** at **Valley View University (VVU)**. This platform combines a dynamic public information portal with a secure, anonymous voting system.

---

## ✨ Key Features

### 🏢 Public Portal
- **Dynamic CMS**: Administrators can update the hero title, subtitle, and featured image in real-time from the dashboard.
- **Responsive Experience**: Fully optimized for mobile, tablet, and desktop with a premium glassmorphic UI.
- **Information Hub**: Easy access to student resources, executive profiles, and general CoSSA information.

### 🗳️ Secure Voting Platform
- **One Student, One Vote**: Enforced through secure student IDs and database-level unique constraints.
- **Live Statistics**: Real-time voter turnout and candidate standings for administrators.
- **Anonymous Balloting**: Votes are recorded without linking them back to individual student identities.
- **Physical Media Support**: Candidates can have high-resolution photos uploaded and stored securely.

### 🛡️ Admin Suite
- **Real-time Oversight**: Dashboard featuring instant turnout calculations and progress visualizers.
- **Batch Management**: Import student credentials using CSV files for quick onboarding.
- **Content Controls**: Manage portfolios, candidate manifestos, and site messaging without writing any code.

---

## 🛠️ Technology Stack

- **Backend**: Python 3.13 / Flask
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Styling**: Tailwind CSS (via CDN)
- **Production Server**: Gunicorn
- **Session Management**: Flask-Login + secure password hashing (Werkzeug)
- **Deployment Ready**: Docker & Coolify optimized

---

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.13+
- PostgreSQL database

### 2. Environment Setup
Create a `.env` file in the root directory:
```env
SECRET_KEY=your_secure_random_key
DATABASE_URL=postgresql://user:password@localhost/cossa_db
# Optional: Set this if deploying to Coolify with persistent storage
UPLOAD_FOLDER=/app/app/static/uploads
```

### 3. Installation
```bash
# Clone the repository
git clone https://github.com/sasusavage/cosaa.git
cd cosaa

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Or venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt
```

### 4. Running the App
```bash
python run.py
```
The app will initialize the database and create a default admin user on the first run:
- **Username**: `admin`
- **Password**: `admin123`

---

## ☁️ Deployment on Coolify

This repository is pre-configured for **Coolify** using the included `Dockerfile`.

1. **Persistent Storage**: Ensure you mount a volume (e.g., `cossa-images`) to the path specified in your `UPLOAD_FOLDER` environment variable (default: `/app/app/static/uploads`).
2. **Environment**: Add your `DATABASE_URL` and `SECRET_KEY` in the Coolify environment settings.
3. **Build**: Coolify will automatically detect the Dockerfile and deploy the WSGI server using Gunicorn.

---

## 📜 License
Developed for CoSSA, Valley View University. Designed for excellence.
