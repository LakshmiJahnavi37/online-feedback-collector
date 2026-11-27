
# Online Feedback Collector

A Flask and SQLite application for collecting user feedback and managing responses through an admin dashboard.

## Features

- User feedback form
- Name and email collection
- 1 to 5 star rating system
- Optional comments
- SQLite database storage
- Admin authentication
- Admin dashboard
- Total feedback count
- Average rating calculation
- Rating chart using Chart.js
- CSV export
- Clear feedback records
- Responsive frontend

## Technologies

- Python
- Flask
- SQLite
- HTML
- CSS
- JavaScript
- Chart.js

## Installation

Install dependencies:

pip install -r requirements.txt

## Run the application

python app.py

Open this URL in your browser:

http://127.0.0.1:5000/

## Admin Login

Open:

http://127.0.0.1:5000/admin-login

For local demonstration, the default credentials are:

Email: admin@example.com
Password: ChangeMe123!

Change the default credentials before using this application with real data.

## Database

SQLite database is automatically created when the application starts.

## Security Notes

- Use a strong SECRET_KEY.
- Change the default admin credentials.
- Never upload database.db or real feedback to a public repository.
- Never commit passwords or .env files.
- Do not enable Flask debug mode on a public server.
- This project is intended as a learning/demo application.
