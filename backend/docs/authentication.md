# Authentication and User Management Module for Smart Traffic Management System

This document outlines the authentication and user management system for the Smart Traffic Management System.

## Overview

The authentication system provides secure user registration, login, and session management using:
- JWT (JSON Web Token) for authentication
- PostgreSQL database for user storage
- bcrypt for secure password hashing
- Express.js for the authentication API

## Features

- User registration with email and password
- Secure login with JWT token generation
- User profile management
- Role-based access control (User/Admin)
- Session tracking
- Password change functionality
- Account deletion
- Integration with Python FastAPI backend

## API Endpoints

| Endpoint | Method | Description | Authentication |
|----------|--------|-------------|----------------|
| `/api/auth/register` | POST | Register a new user | None |
| `/api/auth/login` | POST | Login and get JWT token | None |
| `/api/user/profile` | GET | Get current user profile | JWT |
| `/api/user/profile` | PUT | Update user profile | JWT |
| `/api/user/change-password` | PUT | Change user password | JWT |
| `/api/user/delete-account` | DELETE | Delete user account | JWT |
| `/api/auth/logout` | POST | Logout and invalidate token | JWT |
| `/api/reports/recent` | GET | Get recent traffic reports | JWT |

## Database Schema

```sql
-- User table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(200) NOT NULL,
    role VARCHAR(20) DEFAULT 'user',
    avatar_url VARCHAR(200),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Sessions table for tracking user sessions
CREATE TABLE sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    token VARCHAR(500) NOT NULL,
    ip_address VARCHAR(50),
    device_info VARCHAR(200),
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Traffic reports table
CREATE TABLE traffic_reports (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    location VARCHAR(200) NOT NULL,
    type VARCHAR(50) NOT NULL,
    details JSONB,
    status VARCHAR(20) DEFAULT 'new',
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Authentication Flow

1. User registers or logs in through the frontend interface
2. Authentication server validates credentials and issues a JWT token
3. Frontend stores the token in localStorage
4. For API requests:
   - Frontend includes token in Authorization header
   - Node.js auth-bridge validates the token
   - If valid, the request is forwarded to FastAPI with user info headers
   - FastAPI verifies the presence of user headers
   - User permissions are checked for protected endpoints

## Security Considerations

- Passwords are hashed using bcrypt with appropriate salt rounds
- JWTs have short expiration times
- Rate limiting is applied to prevent brute force attacks
- Input validation is performed on all user inputs
- HTTPS is required for production deployment
- Cross-Origin Resource Sharing (CORS) is configured to prevent unauthorized access
- User roles enforce access control for sensitive operations

## Frontend Integration

- Login/register forms with client-side validation
- JWT stored in localStorage with appropriate security measures
- Automatic redirect to login for protected pages
- User profile management UI
- Conditional rendering based on authentication status

## Backend Integration

- auth-bridge.js connects the authentication server with the Python backend
- Python FastAPI routes use auth middleware for protected endpoints
- Role-based access control for sensitive operations