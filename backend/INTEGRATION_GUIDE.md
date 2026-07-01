# Smart Traffic Management System - Integration Guide

This document pr- **Backend API**: `python run_stms_server.py` (runs on port 8000)vides step-by-step instructions for running the integrated Smart Traffic Management System.

## System Architecture

The system consists of three main components:

1. **Node.js Authentication Server** - Handles user registration, login, and JWT token management
2. **FastAPI Backend Server** - Provides traffic detection and analysis APIs
3. **Frontend Web Server** - Serves the HTML/CSS/JS web interface

## Prerequisites

### Install Node.js and Python
1. **Node.js**: Download and install from [nodejs.org](https://nodejs.org/)
   - Verify installation with: `node --version`
   - Required for full system functionality including authentication and frontend service

2. **Python 3.8+**: Download and install from [python.org](https://www.python.org/downloads/)
   - Verify installation with: `python --version`
   - Required for the backend detection API

### Node.js Dependencies
- Express.js, bcrypt, jsonwebtoken, pg (PostgreSQL client), cors, dotenv
- Install with: `npm install`
- These are required for the authentication server

### Python Dependencies
- FastAPI, uvicorn, opencv-python, numpy, torch, etc.
- Install with: `pip install -r requirements.txt`
- These are required for the backend detection API

### Database
- PostgreSQL database (local or remote)
- Create database with: `psql -c "CREATE DATABASE stms;"`
- Initialize schema with: `psql -d stms -f schema.sql`

## Configuration

### Environment Variables
The project uses a `.env` file for configuration. Make sure it contains:

```
# Database configuration
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=your_password
DB_DATABASE=stms

# JWT Authentication
JWT_SECRET=your_jwt_secret_key
```

## Running the System

### Option 1: All-in-One Script (Requires Node.js)
Run all servers (auth, backend, frontend) with a single command:

```bash
python run_all.py
```

This will start:
- Authentication server on port 3000
- Frontend server on port 5000
- Backend API on port 8000

### Option 2: Individual Servers (Requires Node.js)
If you prefer to run servers individually:

1. **Auth Server**: `node auth-server.js`
2. **Backend API**: `python run_stms_server.py`
3. **Frontend**: `node run_website.js`

### Option 3: Backend-Only Mode (No Node.js Required)
If you don't have Node.js installed or just want to test the backend API:

**On Windows:**
```
run_backend_only.bat
```

**On PowerShell:**
```
.\run_backend_only.ps1
```

This will start only the FastAPI backend server on port 8000.
- Access the API documentation at: http://localhost:8000/docs

## Testing the Integration

1. Open your browser to `http://localhost:5000/system_test.html`
2. This page will run tests on various system components
3. Verify that all services are running correctly

## Manual Testing

1. Open `http://localhost:5000` in your browser
2. Register a new user at `http://localhost:5000/register.html`
3. Login with your credentials at `http://localhost:5000/login.html`
4. Navigate to the dashboard and upload images for detection

## Troubleshooting

### Connection Issues
- Ensure PostgreSQL is running and accessible
- Check that ports 3000, 5000, and 8000 are available

### Authentication Problems
- Verify JWT_SECRET is properly set in .env file
- Check browser console for API errors

### Detection API Issues
- Ensure all Python dependencies are installed
- Check that model files exist in the correct directories