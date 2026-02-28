# Teamflow

Django project with a **core** app for teams, tasks, tags, and feedback.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate   # Windows
# source .venv/bin/activate  # Linux/macOS
pip install -r requirements.txt
```

## Database (PostgreSQL)

Use either **DATABASE_URL** or individual variables.

**Option 1 – DATABASE_URL**
```bash
set DATABASE_URL=postgres://user:password@localhost:5432/teamflow
```

**Option 2 – Individual vars**
```bash
set DB_NAME=teamflow
set DB_USER=your_user
set DB_PASSWORD=your_password
set DB_HOST=localhost
set DB_PORT=5432
```

Optional: `DJANGO_SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS` (comma-separated).

## Run

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Admin: http://127.0.0.1:8000/admin/
