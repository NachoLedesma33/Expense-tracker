# Expense Tracker

Server-side expense tracking app built with Django + Tailwind CSS + HTMX.

## Stack

| Layer | Technology |
|---|---|
| Backend | Django 5.0 |
| Frontend | Tailwind CSS 4, HTMX, Chart.js |
| Database | SQLite (dev) / PostgreSQL (production) |
| Auth | Django native authentication |
| Deployment | Vercel (serverless Python runtime) |

## Features

- **Auth** — register, login, logout with demo quick-login
- **Transactions** — CRUD with HTMX modals, inline edit/delete
- **Advanced filters** — type, category, date range, text search with instant HTMX results
- **CSV export** — download transactions with current filters applied
- **Analytics** — 6 Chart.js charts (income/expense by category, monthly comparison, cumulative balance), category ranking, latest transactions
- **Dashboard / Overview** — balance, income, expenses summary cards and recent transactions
- **User settings** — preferred currency, profile name
- **Dark mode** — persisted in localStorage, toggle from sidebar
- **Pagination** — HTMX-driven, no full page reloads
- **Responsive** — mobile sidebar, adaptive grid layouts
- **Glassmorphism UI** — backdrop blur cards with dark/light mode contrast

## Architecture

```
config/             # Django settings (base / local / production)
core/               # Home view (redirects to transactions)
transactions/       # Transaction + Category models, views, forms
analytics/          # Analytics overview with Chart.js
users/              # Auth views, Profile model, settings form
services/           # Business logic layer (dashboard, filters, analytics, export)
templates/          # Jinja2 templates with partials for HTMX
theme/              # Tailwind CSS source and build
api/                # Vercel serverless handler
static/             # Static assets (JS, CSS, images)
```

## Quick Start

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py tailwind build
python manage.py createsuperuser
python manage.py runserver
```

Login with `admin` / `admin123` (demo credentials pre-filled on login page).

## Environment Variables (Production)

| Variable | Description |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string |
| `DJANGO_SECRET_KEY` | Secret key for cryptographic signing |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated allowed hosts |

## Design Decisions

- **Server-side rendering** — no SPA framework, Django templates + HTMX for interactivity
- **Service layer** — all business logic in `services/`, views stay thin
- **Partial templates** — HTMX targets render small HTML fragments, not JSON
- **Per-user isolation** — every query filtered by `request.user`
- **Glassmorphism** — CSS custom properties for glass effect, easy to theme
- **Settings split** — `base.py` for shared, `local.py` for dev, `production.py` for Vercel
