/**
 * Frontend configuration for Smart Traffic Management System
 * This file exports API base URLs and other configuration settings
 * for frontend components to use when making API calls
 */

// Base URLs for API services (dynamically resolved to current host/port)
export const API_BASE_URL = (typeof window !== 'undefined' ? window.location.origin : '') + '/api/v1';
export const DETECTION_API_URL = API_BASE_URL;

// API endpoints
export const ENDPOINTS = {
    // Auth endpoints
    AUTH: {
        LOGIN: '/api/login',
        REGISTER: '/api/register',
        PROFILE: '/api/profile',
        LOGOUT: '/api/logout'
    },
    
    // Detection endpoints
    DETECTION: {
        OBJECTS: '/detect/objects',
        POTHOLES: '/detect/potholes',
        WEATHER: '/detect/weather',
        TRAFFIC_SIGNS: '/detect/traffic-signs',
        RAILWAY_CROSSING: '/detect/railway-crossing'
    },
    
    // Analytics endpoints
    ANALYTICS: {
        INSIGHTS: '/insights/generate',
        OPTIMIZE: '/optimize/signals',
        STATS: '/analytics/stats'
    }
};

// UI Configuration
export const UI_CONFIG = {
    REFRESH_INTERVAL: 30000, // 30 seconds
    MAX_FILE_SIZE: 5 * 1024 * 1024, // 5MB
    ALLOWED_FILE_TYPES: ['image/jpeg', 'image/png', 'image/webp']
};

// Feature flags
export const FEATURES = {
    ENABLE_LIVE_FEED: false,
    ENABLE_ANALYTICS: true,
    ENABLE_NOTIFICATIONS: false
};
