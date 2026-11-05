# GeoGwalior – GSI Geoscience Museum Portal

A Flask-based digital museum portal for exploring and managing museum artifact records.

## Project structure

```text
GeoGwalior_Corrected_Project/
├── app.py
├── models.py
├── extensions.py
├── requirements.txt
├── templates/
│   ├── index.html
│   ├── base.html
│   ├── login.html
│   ├── dashboard.html
│   ├── add.html
│   ├── artifacts.html
│   └── artifact_detail.html
└── static/
    └── stylesheet.css
```

## Run locally (Windows PowerShell)

1. Install Python 3.10+.
2. Open PowerShell in this project folder.
3. Create and activate a virtual environment:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

4. Install dependencies:

   ```powershell
   pip install -r requirements.txt
   ```

5. Set local environment values for this PowerShell session. Choose your own admin password:

   ```powershell
   $env:FLASK_SECRET_KEY = "replace-this-with-a-long-random-secret"
   $env:ADMIN_USERNAME = "your-admin-username"
   $env:ADMIN_PASSWORD = "choose-a-strong-password"
   ```

6. Start the application:

   ```powershell
   python app.py
   ```

7. Open `http://127.0.0.1:5000`.

The app creates its database tables when started. If the database has no user with the configured `ADMIN_USERNAME`, it creates that admin account using a password hash. No default `admin/admin123` account is created.

For local debugging only, you may set `$env:FLASK_DEBUG = "1"` before running. Do not enable debug mode on a public deployment.

## Before uploading to GitHub

- Do not upload `.env`, `museum.db`, generated Excel/PDF exports, passwords, or secret keys.
- Keep `FLASK_SECRET_KEY` and admin credentials out of source code.
- The database is local SQLite storage and is ignored by `.gitignore`.
- The landing page includes externally hosted images; those image URLs require an internet connection.
