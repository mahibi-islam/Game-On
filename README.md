# GAME ON BOGURA - Turf Booking System

A complete turf booking website built with Flask and MongoDB.

## Project Structure

```
GOB/
├── models/          # All database files
│   ├── booking.py
│   ├── slot.py
│   ├── admin.py
│   └── settings.py
├── routes/          # All routes
│   ├── user_routes.py
│   ├── admin_routes.py
│   └── api_routes.py
├── templates/       # All templates
│   ├── base.html
│   ├── index.html
│   ├── booking.html
│   └── admin/
├── static/          # Static files (CSS, JS, images)
├── app.py           # Flask application
├── config.py        # Configuration
├── db.py            # Database connection
├── run.py           # Application entry point
└── requirements.txt # Dependencies
```

## Quick Start

1. **Install MongoDB** and start the service
2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
3. **Run the application:**
   ```bash
   python run.py
   ```

## Features

- Online booking system
- Admin dashboard
- Excel export
- WhatsApp notifications
- Gallery management
- Payment tracking

