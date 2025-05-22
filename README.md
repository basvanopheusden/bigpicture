# BigPicture

This repository contains a small Flask backend and a React frontend built with Vite.

## Prerequisites
- **Python 3.9+** and `pip` for the backend
- **Node.js 20 LTS** and `npm` for the frontend
- [Docker](https://www.docker.com/) (optional) if you prefer containerized runs

## Running the Backend
1. `cd backend`
2. (optional) create and activate a virtual environment
   ```bash
   python -m venv venv && source venv/bin/activate
   ```
3. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```
4. Start the server
   ```bash
   python app.py
   ```
   The application listens on the port defined by `PORT` (defaults to `8080`).

### Important environment variables
- `PORT` &ndash; port the Flask app listens on (default `8080`)
- `FLASK_ENV` &ndash; Flask environment (`production` by default)
- `FLASK_APP` &ndash; entrypoint used when running via `flask` or gunicorn
- `DATABASE_URL` &ndash; path to the SQLite database. Defaults to `tasks.db` when
  running locally; the Docker images use `/data/tasks.db`.
- `CORS_ORIGINS` &ndash; comma separated list of allowed origins for CORS

### Docker usage
```bash
docker build -t bigpicture-backend ./backend
docker run -p 8080:8080 bigpicture-backend
```

## Running the Frontend
1. `cd frontend`
2. Install dependencies
   ```bash
   npm install
   ```
3. Launch the development server
   ```bash
   npm run dev
   ```
   The dev server runs on [http://localhost:5173](http://localhost:5173).

   If you encounter an error about a missing `@rollup/rollup-*-arm64` module on
   macOS, remove `node_modules` and `package-lock.json`, ensure you are using
   Node.js 20 (e.g. `nvm use 20`), then reinstall with `npm install`.

### Environment variables
- `VITE_API_URL` &ndash; URL of the backend API. If unset, the app falls back to
  `http://localhost:5001` for local development or the production URL when
  deployed.

### Docker usage
```bash
docker build -t bigpicture-frontend ./frontend
docker run -p 80:80 -e VITE_API_URL=http://localhost:8080 bigpicture-frontend
```

## Local deployment with Docker Compose
The repository includes a `docker-compose.yml` file that runs both the backend
and frontend locally.  Build and start the stack with:

```bash
docker compose up --build
```

The frontend is served on [http://localhost:3000](http://localhost:3000) and the
API is available on [http://localhost:8080](http://localhost:8080).

## Running Tests
Execute the backend unit tests using Python's `unittest`:
```bash
python -m unittest discover -s tests
```

## Repository Layout
- `backend/` &ndash; Flask application and Dockerfile
- `frontend/` &ndash; React/Vite frontend and Dockerfile
- `tests/` &ndash; simple API tests

