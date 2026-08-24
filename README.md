# Airport-Management-System
A simple Flask web application for managing airport-related data (flights, passengers, airports, airlines, and pilot/aircraft assignments) backed by a MySQL database.

# Features
Dashboard (/) — Shows record counts for flights, passengers, and airports, plus a preview of the first 5 flight and passenger records.
View records (/view/<table_name>) — Displays all rows from the flight or passenger table in a generic, column-driven table view.
Add records (/add/<table_name>) — Auto-generates a form (based on the table's columns via DESCRIBE) to insert a new row into the flight or passenger table.
Airports (/airports) — Lists all rows in the airport table.
Airlines (/airlines) — Lists all rows in the airline table.
Airline info (/airlines/<airline_key>/info) — Shows details for a specific airline, its upcoming flights, and its available pilots/aircraft. The app auto-detects likely column names (e.g. airline_id, id, code) so it can adapt to slightly different schemas.
Requirements
Python 3.8+
MySQL Server
Python packages:
# bash
  pip install flask mysql-connector-python
# Database Setup

The app expects a MySQL database named airport with (at minimum) the following tables:

flight
passenger
airport
airline
pilot_aircraft

Update the connection details in get_db_connection() inside the main app file to match your environment:

# python
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="your_password_here",
        database="airport"
    )

Security note: The current code has database credentials hardcoded directly in the source file. Before deploying or sharing this project, move credentials to environment variables (e.g. using python-dotenv) and remove any real passwords from the codebase and version control history.

# Project Structure
.
├── app.py                  # Main Flask application (this file)
├── templates/
│   ├── index.html          # Dashboard
│   ├── view_table.html     # Generic table viewer
│   ├── add_record.html     # Generic add-record form
│   ├── airports.html       # Airport listing
│   ├── airlines.html       # Airline listing
│   └── airline_info.html   # Airline detail page
└── README.md

Note: the templates/ folder and its .html files are referenced by the app via render_template but are not included in the provided source — they need to exist for the app to run.

# Running the App
bash
python app.py

By default, Flask runs in debug mode at http://127.0.0.1:5000/.

# Routes Summary
Route	Methods	Description
/	GET	Dashboard with counts and previews
/view/<table_name>	GET	View all records in flight or passenger
/add/<table_name>	GET, POST	Add a new record to flight or passenger
/airports	GET	List all airports
/airlines	GET	List all airlines
/airlines/<airline_key>/info	GET	Airline details, upcoming flights, available pilots
# Known Limitations
SQL injection risk: Table and column names are interpolated directly into SQL strings (e.g. f"DESCRIBE {table_name}", f"SELECT * FROM {table_name}"). While table_name is restricted to a fixed whitelist (flight, passenger) in most routes, this pattern is fragile — any new route reusing these helpers without a similar whitelist would be vulnerable. Query values (like form input) are correctly parameterized with %s placeholders.
Hardcoded credentials: Database credentials are stored in plaintext in the source code.
No input validation: Form submissions in /add/<table_name> are inserted with minimal validation beyond the datetime-local format conversion.
No authentication: All routes are publicly accessible with no login or access control.
Debug mode: app.run(debug=True, ...) should not be used in production, as it can expose sensitive debugging information.
