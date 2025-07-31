# Public Health Intelligence Platform - Windows Setup Guide

## Prerequisites

### Required Software
1. **Python 3.11+** - Download from [python.org](https://www.python.org/downloads/)
   - Make sure to check "Add Python to PATH" during installation
2. **Node.js 18+** - Download from [nodejs.org](https://nodejs.org/)
3. **Git** - Download from [git-scm.com](https://git-scm.com/)
4. **MySQL** (Optional) - Download from [mysql.com](https://dev.mysql.com/downloads/installer/) or use SQLite

## Quick Start (Windows)

### 1. Clone or Download the Project
```cmd
git clone <repository-url>
cd public-health-intelligence-platform
```

### 2. Backend Setup (Windows Command Prompt)
```cmd
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Frontend Setup (Windows Command Prompt)
```cmd
cd frontend
npm install
```

### 4. Start the Application

**Terminal 1 - Backend:**
```cmd
cd backend
venv\Scripts\activate
python src\main.py
```

**Terminal 2 - Frontend:**
```cmd
cd frontend
npm run dev
```

### 5. Access the Application
- Frontend: http://localhost:5173
- Backend API: http://localhost:5000

## Windows-Specific Configuration

### Database Configuration
The application is configured to work with SQLite by default (no additional setup required).

For MySQL on Windows:
1. Install MySQL Server
2. Create a database named `mydb`
3. Update environment variables or use defaults:
   - DB_HOST=localhost
   - DB_PORT=3306
   - DB_USERNAME=root
   - DB_PASSWORD=password
   - DB_NAME=mydb

## Database Migrations (Recommended)

For development, the application automatically creates the database tables using `db.create_all()`. For a more robust setup that handles database schema changes over time, it is highly recommended to use database migrations with `Flask-Migrate`.

### 1. Install Flask-Migrate
This should be added to your `requirements.txt` file.
```cmd
pip install Flask-Migrate
```

### 2. Initialize the Migration Repository
Run this command **once** in the `backend` directory to create the `migrations` folder.
```cmd
venv\Scripts\activate
set FLASK_APP=src/main.py
flask db init
```

### 3. Create and Apply Migrations
Whenever you change your database models (e.g., in `src/models/database.py`), you need to create a new migration script and apply it to the database.

**Create a migration script:**
```cmd
flask db migrate -m "A short description of the changes"
```

**Apply the migration to the database:**
```cmd
flask db upgrade
```

### Environment Variables (Windows)
Create a `.env` file in the backend directory:
```
DB_HOST=localhost
DB_PORT=3306
DB_USERNAME=root
DB_PASSWORD=password
DB_NAME=mydb
SECRET_KEY=your-secret-key-here
```

### PowerShell Setup (Alternative)
If using PowerShell instead of Command Prompt:

**Backend:**
```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python src\main.py
```

**Frontend:**
```powershell
cd frontend
npm install
npm run dev
```

## Troubleshooting Windows Issues

### Python Virtual Environment Issues
If `venv\Scripts\activate` doesn't work:
```cmd
# Try this instead:
venv\Scripts\activate.bat

# Or use Python directly:
venv\Scripts\python.exe src\main.py
```

### PowerShell Execution Policy
If PowerShell blocks script execution:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Port Conflicts
If ports 5000 or 5173 are in use:
- Backend: Edit `src\main.py` and change `port=5000` to another port
- Frontend: Edit `package.json` and modify the dev script

### Path Issues
All file paths in the code use forward slashes `/` which work on Windows with Python and Node.js. No changes needed.

## Windows Batch Scripts

### start-backend.bat
```batch
@echo off
cd /d "%~dp0backend"
call venv\Scripts\activate.bat
python src\main.py
pause
```

### start-frontend.bat
```batch
@echo off
cd /d "%~dp0frontend"
npm run dev
pause
```

### setup.bat (Complete Setup)
```batch
@echo off
echo Setting up Public Health Intelligence Platform...

echo.
echo Setting up Backend...
cd backend
python -m venv venv
call venv\Scripts\activate.bat
pip install -r requirements.txt
cd ..

echo.
echo Setting up Frontend...
cd frontend
npm install
cd ..

echo.
echo Setup complete!
echo.
echo To start the application:
echo 1. Run start-backend.bat
echo 2. Run start-frontend.bat
echo 3. Open http://localhost:5173 in your browser
pause
```

## Dependencies Verified for Windows

### Backend Dependencies (requirements.txt)
All packages are Windows-compatible:
- Flask==3.1.0
- flask-cors==6.0.0
- Flask-SQLAlchemy==3.1.1
- PyJWT==2.10.1
- pandas==2.3.0
- scikit-learn==1.7.0
- scipy==1.15.3
- numpy==2.3.0
- python-dateutil==2.9.0.post0

### Frontend Dependencies
All npm packages work on Windows:
- React 19.1.0
- Vite 6.3.5
- Tailwind CSS
- Lucide React (icons)
- shadcn/ui components

## Testing on Windows

### Smoke Test (Manual)
This script verifies that the project files are in place and that the backend and frontend can start and build. Run this from the project's root directory.
```cmd
python integration_test.py
```

### Frontend Test
```cmd
cd frontend
npm run dev
# Open http://localhost:5173 in browser
```

## Windows Performance Tips

1. **Use Windows Terminal** for better experience
2. **Exclude project folder** from Windows Defender real-time scanning
3. **Use SSD** for better Node.js performance
4. **Close unnecessary applications** when running simulations

## Common Windows Errors and Solutions

### Error: "python is not recognized"
- Reinstall Python and check "Add to PATH"
- Or use full path: `C:\Python311\python.exe`

### Error: "npm is not recognized"
- Reinstall Node.js
- Restart Command Prompt after installation

### Error: "Access denied" when creating venv
- Run Command Prompt as Administrator
- Or use a different directory with write permissions

### Error: MySQL connection failed
- Ensure MySQL service is running
- Check Windows Firewall settings
- Use SQLite instead (no setup required)

## Windows-Specific Features

### Windows Service (Optional)
To run as Windows service, install:
```cmd
pip install pywin32
```

### Windows Notifications
The platform can integrate with Windows notifications for simulation completion alerts.

### File Associations
Associate `.phip` files with the platform for easy data import.

## Support

For Windows-specific issues:
1. Check Windows Event Viewer for detailed error logs
2. Ensure all prerequisites are properly installed
3. Try running as Administrator if permission issues occur
4. Use Windows-compatible paths (backslashes work, but forward slashes are preferred)
