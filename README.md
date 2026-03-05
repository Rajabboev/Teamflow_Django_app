# Teamflow — Team Task Management App

A lightweight Django web application for managing teams, tasks, and feedback in small engineering teams.

**Live app:** https://teamflowa.uz

---

## Features

- User authentication (login, logout, registration)
- Role-based access: Team Lead and Member
- Team creation and member management
- Task creation with priority, deadline, status, and tags
- Feedback and rating system per task
- Personal dashboard with task counters

## Technologies

- **Backend:** Django 5, Gunicorn
- **Database:** PostgreSQL 15
- **Frontend:** Bootstrap 5
- **Containerization:** Docker, Docker Compose
- **Web server:** Nginx
- **CI/CD:** GitHub Actions
- **Registry:** Docker Hub
- **Hosting:** Google Cloud Compute Engine

## Local Setup
```bash
git clone https://github.com/Rajabboev/Teamflow_Django_app.git
cd Teamflow_Django_app
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

## Environment Variables

Create a `.env` file in the project root:
```
SECRET_KEY=your-secret-key
DEBUG=False
ALLOWED_HOSTS=teamflowa.uz,www.teamflowa.uz
DB_NAME=teamflow
DB_USER=postgres
DB_PASSWORD=yourpassword
DB_HOST=db
DB_PORT=5432
```

## Docker Deployment
```bash
docker compose up -d
```

## CI/CD Pipeline

Every push to `main` automatically:
1. Runs tests and linting (flake8, black, pytest)
2. Builds and pushes Docker image to Docker Hub
3. Deploys to Google Cloud VM via SSH
4. Runs migrations and collects static files
5. Health checks `https://teamflowa.uz/health/`

## Links

- Live app: https://teamflowa.uz
- Docker Hub: https://hub.docker.com/r/admin1208/teamflow

## Test Credentials

| Username | Password | Role |
|----------|----------|------|
| lead1 | password123 | Team Lead |
| member1 | password123 | Member |
