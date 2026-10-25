# Integrated Tourism Assistance and Rural Transportation Application — Backend

> **🚧 Status: In active development.** This is a final-year capstone project built by a team; this backend specifically is designed and maintained by me. Expect incomplete features, rough edges, and breaking changes. Not production-ready.

This is a queue-based autorickshaw ride-hailing platform designed for rural Kerala, India, with an integrated local tourism module. Unlike typical nearest-driver matching, the system uses a **stand-based dispatch model**: drivers wait at established auto stands (as they do in practice), and the system finds the nearest stand with available drivers, dispatching from a FIFO queue.

This repository contains **only the Django backend API**. The project also includes a separate Go-based tourism read-service and two Android client apps (passenger + driver), maintained separately and not yet public.

---

## Android Demo Video Link

[![Watch the demo](https://img.youtube.com/vi/QkqFf1O8AhM/hqdefault.jpg)](https://youtube.com/shorts/QkqFf1O8AhM)

---

## Table of Contents

- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Key Features](#key-features)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Environment Variables](#environment-variables)
- [API Documentation](#api-documentation)
- [Known Limitations](#known-limitations)

---

## Architecture

The backend is a Django REST API that coordinates several self-hosted services rather than relying on paid third-party APIs:

```
                      ┌─────────────────┐
                      │   Android Apps   │  (passenger + driver, separate repos)
                      └────────┬─────────┘
                               │ REST / JWT
                      ┌────────▼─────────┐
                      │  Django Backend   │  ← this repo
                      │   (DRF + GeoDjango)│
                      └───┬───┬───┬───┬───┘
                          │   │   │   │
            ┌─────────────┘   │   │   └─────────────┐
            ▼                 ▼   ▼                  ▼
     ┌─────────────┐   ┌──────────┐   ┌─────────┐   ┌──────────────┐
     │ PostgreSQL   │   │  Redis   │   │  OSRM   │   │ Firebase FCM │
     │ + PostGIS    │   │ (queue + │   │(routing)│   │(notifications)│
     │ (primary DB) │   │  cache)  │   │         │   │              │
     └─────────────┘   └──────────┘   └─────────┘   └──────────────┘
                          │
                          ▼
                     ┌──────────┐
                     │  Celery  │  (async timeout/dispatch tasks)
                     └──────────┘
```

**None of the infrastructure services above (PostgreSQL, Redis, OSRM, MinIO) are bundled in this repo.** You'll need your own running instances — see [Getting Started](#getting-started).

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | Django + Django REST Framework |
| Database | PostgreSQL + PostGIS (geospatial queries) |
| Cache / Queue | Redis (sorted sets for FIFO dispatch queues) |
| Async tasks | Celery (broker: Redis) |
| Auth | JWT via `djangorestframework-simplejwt` |
| Push notifications | Firebase Cloud Messaging (`firebase-admin`) |
| Routing | Self-hosted OSRM (Docker, Kerala OSM extract) |
| Object storage | S3-compatible (MinIO) via `django-storages` + `boto3` |
| API docs | `drf-spectacular` (OpenAPI / Swagger UI) |

## Key Features

- **Stand-based FIFO dispatch** — Redis sorted sets, millisecond-timestamp scoring, per-stand queues
- **Two-step booking flow** — fare/route estimate, then confirm; two-leg fare calculation (stand → pickup → destination) via OSRM
- **Dual-role accounts** — a single phone number can hold both a passenger and a driver profile
- **Driver approval workflow** — drivers must be approved by an admin before entering a queue; changing home stand resets approval
- **Timeout & re-queue logic** — Celery-driven dispatch timeout, offline-driver detection via heartbeat, automatic re-queueing on timeout/decline
- **Separate login flows** — dedicated endpoints for passenger vs. driver apps, so a passenger account can't log into the driver app and vice versa
- **Auto-generated stand codes** — `{state}{district}{sequence}`, e.g. `KLKN0001`

## Project Structure

```
backend/
├── users/      — Custom User model, registration & login
├── drivers/    — DriverProfile, driver registration & login, driver details
├── stands/     — Stand, District, State models, queue logic, stand selection
├── rides/      — Ride, DriverRequest, FareConfig, ride lifecycle & fare calc
├── core/       — Shared permissions, Redis client, custom exceptions, storage backends
└── tourism/    — Place, PlaceImage, Rating models (tourism module)
```

## Getting Started

### Prerequisites

- Python 3.10+
- PostgreSQL with the **PostGIS** extension enabled
- A running **Redis** server
- A running **OSRM** instance (self-hosted; used for routing and fare calculation — not included here)
- A **Firebase** project with a service account (for push notifications — optional if you're not testing FCM)
- An S3-compatible object store such as **MinIO** (for media storage)

> **Windows users:** GeoDjango requires GDAL/GEOS binaries on your `PATH`. This repo assumes a standard PostgreSQL Windows install; you may need to adjust the GDAL/GEOS paths in `settings.py` to match your own install location.

### Installation

```bash
git clone <repo-url>
cd backend

python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env          # then fill in your actual values
```

Place your Firebase service account credentials at the project root as `serviceAccountKey.json` (this file is gitignored and won't be committed).

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

### Running Celery

Celery handles async ride-dispatch timeouts and must run alongside the Django server:

```bash
# Linux / macOS
celery -A backend worker --loglevel=info

# Windows (the default prefork pool isn't supported — use solo)
celery -A backend worker --loglevel=info --pool=solo
```

## Environment Variables

See `.env.example` for the full list. At minimum you'll need:

| Variable | Purpose |
|---|---|
| `SECRET_KEY` | Django secret key |
| `DEBUG` | `True` for local development |
| `ALLOWED_HOSTS` | Comma-separated allowed hosts |
| `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` | PostgreSQL connection |
| `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY`, `MINIO_ENDPOINT`, `MINIO_PUBLIC_BUCKET`, `MINIO_PRIVATE_BUCKET` | Object storage |
| `OSRM_URL` | Your running OSRM instance, e.g. `http://localhost:5000` |

## API Documentation

Once the server is running, interactive API docs (Swagger UI) are available at:

```
http://localhost:8000/api/docs/
```

## Known Limitations

This is an active capstone project, not a finished product. In particular:

- No CI/CD or automated test suite yet
- Live driver location tracking (via WebSockets) is planned but not implemented
- Deployment/infra configuration (Docker Compose, reverse proxy, etc.) is intentionally not included in this repo
- The tourism module's Go read-service and the Android clients are maintained separately

---

Built by Rich as a final-year capstone project. Questions or feedback welcome — feel free to open an issue.
