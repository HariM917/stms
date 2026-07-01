# Smart Traffic Management System (STMS)

Welcome to the Smart Traffic Management System (STMS) repository. This project is a comprehensive solution for monitoring and managing traffic, featuring both a robust backend and an interactive frontend.

## Project Structure

The repository is structured into two main components:

- **`/backend`**: Contains the server-side code, built with Python. It handles traffic data processing, object detection, AI models, and provides the API endpoints.
- **`/frontend`**: Contains the client-side code, built with HTML, CSS (Bootstrap), and JavaScript. It provides a user-friendly interface for monitoring dashboards, reporting, and government portals.

## Getting Started

### Prerequisites

Ensure you have the following installed on your local machine:
- Python (for the backend)
- Node.js & npm (for frontend dependencies, if applicable)
- Docker & Docker Compose (optional, for containerized execution)

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   # On Windows:
   .venv\Scripts\activate
   # On Mac/Linux:
   source .venv/bin/activate
   ```
3. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the backend server (e.g., using Uvicorn or FastAPI):
   ```bash
   uvicorn app.main:app --reload
   ```

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Open `index.html` or `landing.html` in your browser to view the application, or serve it using a local development server (like Live Server or Python's `http.server`):
   ```bash
   python -m http.server 8000
   ```

## Docker (Optional)

You can also run the entire application using Docker Compose:

```bash
docker-compose up --build
```

## Contributing

Contributions are welcome! Please create a new branch for any feature or bug fix and submit a pull request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.