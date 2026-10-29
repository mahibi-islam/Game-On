# GAME ON - Sports Venue & Turf Booking Platform

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0.3-000000?style=flat&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![MongoDB](https://img.shields.io/badge/MongoDB-PyMongo-47A248?style=flat&logo=mongodb&logoColor=white)](https://www.mongodb.com/)
[![License](https://img.shields.io/badge/License-Proprietary-blue.svg)](#)

A full-featured sports venue and turf booking platform built with Flask and MongoDB. The system supports multi-location venue management, real-time slot booking, dynamic weekday/weekend pricing, user authentication, role-based administration, automated Google Sheets & Excel synchronization, and instant email/WhatsApp notifications.

---

## Table of Contents

- [What It Does](#what-it-does)
- [Technology Stack](#technology-stack)
- [Project Architecture](#project-architecture)
- [Prerequisites](#prerequisites)
- [Local Setup & How to Run](#local-setup--how-to-run)
- [Environment Variables Guide](#environment-variables-guide)
- [Initial Admin Setup](#initial-admin-setup)
- [Security Features](#security-features)
- [Production Deployment](#production-deployment)
- [Maintenance & Scripts](#maintenance--scripts)

---

## What It Does

### Customer Portal
- **Real-Time Availability**: Customers can check live availability for different sports (Football, Badminton) across multiple venues (e.g., Bogura Gohail Road, Khulna Sadar).
- **Dynamic Pricing & Discounts**: Automatically calculates pricing based on weekday vs. weekend rates and active promotional discounts.
- **User Authentication**: Secure user registration, login, and token-based password reset via automated emails.
- **Booking Checkout**: Online slot reservation with bKash, Nagad, or Cash payment options, transaction ID input, and custom booking notes.
- **Customer Profiles**: View booking history, approval status (pending, approved, paid, cancelled), and details.
- **Notifications**: Automated responsive HTML confirmation emails sent directly to the customer and venue management upon booking, plus one-click WhatsApp notification links.

### Admin Dashboard
- **Role-Based Access Control**:
  - **Super Administrator**: Complete oversight of all venues, slots, settings, admins, and financials.
  - **Branch / Location Admins**: Scoped access restricted to managing bookings and slots for their assigned venue.
- **Booking Management**: Interactive dashboard to review, approve, mark paid, reject, or cancel reservations, with filtering by venue, date, and status.
- **Slot Scheduling**: Create, configure, enable/disable, and price slots with weekday and weekend rate variations.
- **Venue & Location Management**: Add and customize venue branches, phone numbers, addresses, ground rules, and toggle online bookings per venue.
- **Live Google Sheets & Excel Sync**: Every booking is recorded to both a local Excel file (`bookings.xlsx`) and synced directly to a live Google Sheet via Google Service Accounts.
- **Gallery & Carousel CMS**: Upload images and videos to the homepage carousel and gallery, with local storage or optional Cloudinary CDN hosting.
- **Customer Messages**: Centralized inbox for inquiries submitted through the contact form.

---

## Technology Stack

| Layer | Technology | Description |
| :--- | :--- | :--- |
| **Backend Framework** | **Flask 3.0.3** | Python microframework with application factory and modular blueprints |
| **Database** | **MongoDB** | Document database using `Flask-PyMongo` & `pymongo 4.6.3` |
| **Authentication & Security** | **Werkzeug & Flask-WTF** | PBKDF2 SHA-256 password hashing, CSRF token validation on all forms and fetch requests |
| **Rate Limiting** | **Flask-Limiter 3.8.0** | IP-based request rate limiting with `ProxyFix` reverse-proxy support |
| **Spreadsheet Sync** | **OpenPyXL & gspread** | Local Excel read/write (`openpyxl`) and Google Sheets API integration (`gspread`, `google-auth`) |
| **Email Service** | **SMTP & Gmail API** | Dual-mode email engine supporting standard SMTP (Gmail/TLS) and Google Gmail API |
| **Cloud Media** | **Cloudinary (Optional)** | Optional cloud storage for gallery and carousel media |
| **Frontend** | **HTML5, CSS3, JS** | Vanilla CSS with glassmorphism/dark theme, responsive mobile navigation, and AJAX fetch CSRF wrapper |
| **WSGI Server** | **Gunicorn / Waitress** | `gunicorn` for Unix/Linux production, `waitress` for Windows environments |

---

## Project Architecture

```
GOB/
├── app.py                      # Application factory (create_app), extensions, error handlers & headers
├── config.py                   # Development, Production, and Testing configuration classes
├── db.py                       # Global extension instances (PyMongo, Limiter, CSRFProtect)
├── run.py                      # Application entry point for development & production servers
├── requirements.txt            # Python dependencies
├── Procfile                    # Process file for cloud hosting (e.g., Gunicorn on Render/Heroku)
├── .env.example                # Template of all environment variables (no secrets committed)
├── .gitignore                  # Git ignore rules protecting all secrets, tokens, and logs
│
├── models/                     # Data models and database interactions
│   ├── admin.py                # Admin user model, roles, and credential verification
│   ├── booking.py              # Booking lifecycle, Excel export, and Google Sheets sync
│   ├── contact_message.py      # Contact form submissions
│   ├── location.py             # Venue locations and branch configuration
│   ├── settings.py             # Global turf info, contacts, and homepage CMS
│   ├── slot.py                 # Time slots, weekday/weekend pricing, and discount logic
│   └── user.py                 # Customer accounts, sessions, and password reset tokens
│
├── routes/                     # Blueprint routes
│   ├── admin_routes.py         # Admin dashboard, bookings, slots, gallery, and settings
│   ├── api_routes.py           # REST endpoints for slot availability and booking submission
│   ├── auth_routes.py          # Customer & admin authentication, registration, password reset
│   └── user_routes.py          # Public pages (home, booking, profile, gallery, facilities, contact)
│
├── utils/                      # Helper utilities
│   ├── email_utils.py          # SMTP & Gmail API delivery, HTML templates for customer/admin alerts
│   └── slot_utils.py           # Timezone handling (Asia/Dhaka), slot formatting, and validation
│
├── scripts/                    # Maintenance and operational scripts
│   └── backfill_ids.py         # Sequential booking ID migration utility
│
├── static/                     # Static assets
│   ├── css/                    # Stylesheets (modern.css, admin.css, style.css)
│   ├── js/                     # Client scripts (csrf.js, main.js)
│   ├── images/                 # Brand assets and logos
│   └── carousel/               # Default homepage carousel images
│
└── templates/                  # Jinja2 HTML templates
    ├── base.html               # Public base layout
    ├── index.html              # Landing page
    ├── booking.html            # Interactive slot reservation interface
    ├── admin/                  # Admin portal templates (dashboard, bookings, slots, users, etc.)
    └── auth/                   # Authentication templates (login, signup, password reset)
```

---

## Prerequisites

Before running the application, make sure you have:

1. **Python 3.10 or higher** installed.
2. **MongoDB** installed and running locally on port `27017`, OR a free cloud connection string from [MongoDB Atlas](https://www.mongodb.com/atlas).
3. **Git** for version control.

---

## Local Setup & How to Run

Follow these steps to set up and run the application locally:

### 1. Clone the Repository
```bash
git clone https://github.com/SheikhTrump/Game-On.git
cd Game-On
```

### 2. Create and Activate a Virtual Environment

**On Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**On Windows (Command Prompt):**
```cmd
python -m venv venv
.\venv\Scripts\activate.bat
```

**On macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Create your local `.env` file by copying the provided `.env.example` template:

**On Windows:**
```cmd
copy .env.example .env
```

**On macOS / Linux:**
```bash
cp .env.example .env
```

Open `.env` in your text editor and fill in your values. At a minimum for local development:
```ini
FLASK_ENV=development
FLASK_DEBUG=True
SECRET_KEY=dev-secret-key-replace-in-production
MONGO_URI=mongodb://localhost:27017/turf_booking
ADMIN_PASSWORD=your_secure_admin_password
```

*(See [Environment Variables Guide](#environment-variables-guide) below for complete details).*

### 5. Start the Application
```bash
python run.py
```

The application will start on `http://127.0.0.1:5000` (or `http://localhost:5000`).

### 6. Accessing the Application
- **Customer Website**: Open [http://localhost:5000](http://localhost:5000)
- **Admin Panel**: Open [http://localhost:5000/admin/login](http://localhost:5000/admin/login)
  - Default Username: `admin` (or the value set in `ADMIN_USERNAME`)
  - Password: the password you specified in `ADMIN_PASSWORD` in your `.env`

---

## Environment Variables Guide

All sensitive credentials and environment configurations are managed via environment variables.

| Variable | Required | Default | Description |
| :--- | :---: | :--- | :--- |
| `SECRET_KEY` | **Yes (Prod)** | Dev default fallback | Secret key used for session signing and CSRF security. Required in production. |
| `FLASK_ENV` | No | `development` | Environment mode (`development`, `production`, `testing`). |
| `FLASK_DEBUG` / `DEBUG` | No | `False` | Enables Flask debug mode with auto-reload. |
| `PORT` | No | `5000` | Port on which the application listens. |
| `MONGO_URI` | **Yes (Prod)** | `mongodb://localhost:27017/turf_booking` | MongoDB connection string (local or MongoDB Atlas URI). |
| `ADMIN_USERNAME` | No | `admin` | Username for the initial superadmin account. |
| `ADMIN_PASSWORD` | No | *None* | Password used when the superadmin account is first created. |
| `ADMIN_BOGURA_PASSWORD` | No | Fallback to `ADMIN_PASSWORD` | Initial password for the Bogura branch admin (`admin_bogura`). |
| `ADMIN_KHULNA_PASSWORD` | No | Fallback to `ADMIN_PASSWORD` | Initial password for the Khulna branch admin (`admin_khulna`). |
| `EMAIL_HOST` | No | `smtp.gmail.com` | SMTP host for email notifications. |
| `EMAIL_PORT` | No | `587` | SMTP port (e.g., `587` for TLS or `465` for SSL). |
| `EMAIL_USERNAME` | No | *None* | Email address used for authentication. |
| `EMAIL_PASSWORD` | No | *None* | Email account password or 16-character App Password. |
| `EMAIL_SENDER` | No | Fallback to `EMAIL_USERNAME` | Sender address shown on outgoing emails. |
| `GOOGLE_SHEETS_URL` | No | *None* | URL of the Google Sheet for real-time booking synchronization. |
| `GOOGLE_SHEETS_CREDENTIALS_FILE` | No | `credentials.json` | Path to Google Service Account JSON file. |
| `GOOGLE_CREDENTIALS_JSON` | No | *None* | Raw JSON string of Google Service Account credentials (ideal for cloud/PaaS). |
| `GOOGLE_TOKEN_FILE` | No | `token.json` | Path to Google Gmail API OAuth 2.0 user credentials file. |
| `GOOGLE_TOKEN_JSON` | No | *None* | Raw JSON string of Gmail API user credentials. |
| `CLOUDINARY_URL` | No | *None* | Cloudinary connection string for cloud media uploads. |
| `RATELIMIT_STORAGE_URI` | No | `memory://` | Storage backend for rate limiting (e.g., `memory://` or `redis://...`). |
| `PROXY_COUNT` | No | `1` | Number of reverse proxies (e.g., Render/Nginx router) for client IP detection. |
| `UPLOAD_FOLDER` | No | `static/uploads` | Local directory for uploaded files. |
| `EXCEL_FILE` | No | `bookings.xlsx` | Filename/path for local Excel backup exports. |

---

## Initial Admin Setup

When the application boots for the first time, it seeds default data (locations, default slots, settings, and administrator accounts):

1. Set `ADMIN_PASSWORD=YourSecurePasswordHere` in your `.env` file before launching.
2. Run `python run.py`.
3. The application will create:
   - Superadmin: Username `admin`
   - Bogura Admin: Username `admin_bogura`
   - Khulna Admin: Username `admin_khulna`
4. Log in at `/admin/login` and manage additional admins or reset passwords under **Admin > Users**.

---

## Security Features

- **No Secrets in Source Control**: All sensitive values (passwords, tokens, database URIs, API keys) are loaded strictly from environment variables. Git ignore rules prevent accidental commits of `.env` and credential files.
- **CSRF Protection**: `Flask-WTF` enforces CSRF tokens across all standard forms and asynchronous `fetch()` API calls via `csrf.js`.
- **Password Security**: Passwords are never stored in plaintext; they are hashed with PBKDF2 SHA-256 via Werkzeug.
- **Rate Limiting**: Protects sensitive endpoints (e.g., booking creation, authentication) against abuse and denial of service.
- **Reverse Proxy Safety**: Uses `werkzeug.middleware.proxy_fix.ProxyFix` with configurable `PROXY_COUNT` to securely parse client IP addresses without trusting unverified host headers.
- **Security Headers**: Injects `X-Content-Type-Options: nosniff`, `X-Frame-Options: SAMEORIGIN`, `X-XSS-Protection`, and `Referrer-Policy`.
- **RFC 9116 Compliant**: Provides `/.well-known/security.txt` and a comprehensive `robots.txt` blocking unauthorized AI scrapers.

---

## Production Deployment

### 1. Procfile & Gunicorn
A `Procfile` is included for deployment on platforms like Render, Heroku, or Railway:
```
web: gunicorn run:app
```

### 2. Environment Configuration
When deploying to production:
1. Set `FLASK_ENV=production`.
2. Generate a cryptographically secure `SECRET_KEY`:
   ```bash
   python -c "import secrets; print(secrets.token_hex(32))"
   ```
3. Set your production `MONGO_URI` (e.g., MongoDB Atlas).
4. Set `SESSION_COOKIE_SECURE=True` (automatically enforced when `FLASK_ENV=production` and served over HTTPS).
5. If using Google Sheets sync without committing files, paste the entire service account JSON into the `GOOGLE_CREDENTIALS_JSON` environment variable in your host's dashboard.

---

## Maintenance & Scripts

### Backfilling Booking IDs
If legacy bookings exist without sequential booking identifiers (`GAMEON#...`), run the included backfill script:
```bash
python -m scripts.backfill_ids
```
This inspects existing bookings and assigns sequential IDs while keeping MongoDB sequence counters in sync.

---

## License

This project is proprietary. All rights reserved.
