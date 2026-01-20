# Environment Configuration Setup

This project now uses environment variables for configuration.

## Setup Steps

### 1. Create .env file
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

### 2. Configure MongoDB
Update `MONGO_URI` in `.env` with your MongoDB connection string:
```
MONGO_URI=mongodb://localhost:27017/turf_booking
```

### 3. Set Secrets
Generate a secure secret key for production:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```
Update `.env` with:
```
SECRET_KEY=paste_generated_key_here
ADMIN_PASSWORD=your_secure_admin_password
```

### 4. Google Sheets Integration (Optional)

To sync bookings to Google Sheets:

#### Step 1: Create Google Cloud Project
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable Google Sheets API and Google Drive API

#### Step 2: Create Service Account
1. Go to "IAM & Admin" > "Service Accounts"
2. Create a new service account
3. Download the JSON credentials file
4. Save it as `credentials.json` in your project root

#### Step 3: Share Your Google Sheet
1. Create a new Google Spreadsheet
2. Copy the spreadsheet URL
3. Share the sheet with the service account email (found in credentials.json)
4. Give "Editor" permissions

#### Step 4: Update .env
```
GOOGLE_SHEETS_URL=https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit
GOOGLE_SHEETS_CREDENTIALS_FILE=credentials.json
```

### 5. Install Dependencies
```bash
pip install -r requirements.txt
```

### 6. Run the Application

**Development:**
```bash
python run.py
```

**Production:**
Use a WSGI server like Gunicorn (Linux/Mac) or Waitress (Windows).

**Windows (using Waitress):**
```bash
waitress-serve --port=5000 run:app
```

**Linux (using Gunicorn):**
```bash
export FLASK_ENV=production
gunicorn -w 4 -b 0.0.0.0:5000 run:app
```

## Important Notes

- **Never commit `.env` or `credentials.json`** to version control
- The app will work with local Excel file if Google Sheets is not configured
- Both local Excel and Google Sheets will be updated simultaneously when both are configured
- Add `.env` and `credentials.json` to your `.gitignore`
