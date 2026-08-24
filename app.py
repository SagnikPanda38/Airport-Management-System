from flask import Flask, render_template, request, redirect, url_for
import mysql.connector

app = Flask(__name__)

# Database Configuration
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Chandan1504$",
        database="airport"
    )

def get_table_columns(cursor, table_name):
    cursor.execute(f"DESCRIBE {table_name}")
    return [col['Field'] for col in cursor.fetchall()]

def first_existing_column(columns, candidates):
    lowered = {col.lower(): col for col in columns}
    for candidate in candidates:
        if candidate.lower() in lowered:
            return lowered[candidate.lower()]
    return None

@app.route('/')
def index():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # Get Counts
        cursor.execute("SELECT COUNT(*) as total FROM flight")
        f_count = cursor.fetchone()['total']
        
        cursor.execute("SELECT COUNT(*) as total FROM passenger")
        p_count = cursor.fetchone()['total']

        cursor.execute("SELECT COUNT(*) as total FROM airport")
        a_count = cursor.fetchone()['total']

        # Previews
        cursor.execute("SELECT * FROM flight LIMIT 5")
        flights = cursor.fetchall()
        
        cursor.execute("SELECT * FROM passenger LIMIT 5")
        passengers = cursor.fetchall()

        cursor.execute("DESCRIBE flight")
        flight_columns = [col['Field'] for col in cursor.fetchall()]

        return render_template('index.html', f_count=f_count, p_count=p_count, 
                               flights=flights, passengers=passengers,
                               flight_columns=flight_columns, a_count=a_count)
    except Exception as e:
        return f"Database Error: {e}"
    finally:
        cursor.close()
        conn.close()

@app.route('/view/<table_name>')
def view_table(table_name):
    if table_name not in ['flight', 'passenger']:
        return "Access Denied", 403
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(f"DESCRIBE {table_name}")
        columns = [col['Field'] for col in cursor.fetchall()]
        
        cursor.execute(f"SELECT * FROM {table_name}")
        data = cursor.fetchall()
        
        return render_template('view_table.html', table_name=table_name, data=data, columns=columns)
    finally:
        cursor.close()
        conn.close()

@app.route('/add/<table_name>', methods=['GET', 'POST'])
def add_record(table_name):
    if table_name not in ['flight', 'passenger']:
        return "Access Denied", 403

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Get column names to build the form
    cursor.execute(f"DESCRIBE {table_name}")
    columns = [col['Field'] for col in cursor.fetchall()]

    if request.method == 'POST':
        # Collect data from form using column names as keys
        row_data = []
        for col in columns:
            value = request.form.get(col)
            # HTML datetime-local uses "YYYY-MM-DDTHH:MM"; convert to MySQL format.
            if value and "T" in value:
                value = value.replace("T", " ")
            row_data.append(value)
        
        # Build dynamic SQL
        placeholders = ", ".join(["%s"] * len(columns))
        col_names = ", ".join(columns)
        query = f"INSERT INTO {table_name} ({col_names}) VALUES ({placeholders})"
        
        try:
            cursor.execute(query, tuple(row_data))
            conn.commit() # Save to MySQL
            return redirect(url_for('index'))
        except Exception as e:
            return f"Error: {e}"
        finally:
            cursor.close()
            conn.close()

    return render_template('add_record.html', table_name=table_name, columns=columns)

@app.route('/airports')
def airports():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("DESCRIBE airport")
        columns = [col['Field'] for col in cursor.fetchall()]

        cursor.execute("SELECT * FROM airport")
        airports_data = cursor.fetchall()

        return render_template('airports.html', columns=columns, airports=airports_data)
    except Exception as e:
        return f"Database Error: {e}"
    finally:
        cursor.close()
        conn.close()

@app.route('/airlines')
def airlines():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        columns = get_table_columns(cursor, "airline")
        cursor.execute("SELECT * FROM airline")
        airlines_data = cursor.fetchall()
        return render_template('airlines.html', columns=columns, airlines=airlines_data)
    except Exception as e:
        return f"Database Error: {e}"
    finally:
        cursor.close()
        conn.close()

@app.route('/airlines/<airline_key>/info')
def airline_info(airline_key):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        airline_columns = get_table_columns(cursor, "airline")
        airline_id_col = first_existing_column(
            airline_columns, ["airline_id", "id", "airlineid", "airline_code", "code", "name", "airline_name"]
        )
        if not airline_id_col:
            return "Could not identify airline key column in airline table."

        cursor.execute(f"SELECT * FROM airline WHERE {airline_id_col} = %s", (airline_key,))
        airline = cursor.fetchone()
        if not airline:
            return "Airline not found.", 404

        flights = []
        pilots = []
        flight_error = None
        pilot_error = None

        try:
            flight_columns = get_table_columns(cursor, "flight")
            flight_airline_col = first_existing_column(
                flight_columns, ["airline_id", "airlineid", "airline", "airline_code", "airline_name", "operator"]
            )
            flight_time_col = first_existing_column(
                flight_columns, ["departure_time", "departure_datetime", "departure_date", "flight_time", "date_time", "departure"]
            )

            if flight_airline_col:
                if flight_time_col:
                    query = f"SELECT * FROM flight WHERE {flight_airline_col} = %s AND {flight_time_col} >= NOW() ORDER BY {flight_time_col} ASC"
                    cursor.execute(query, (airline_key,))
                else:
                    query = f"SELECT * FROM flight WHERE {flight_airline_col} = %s"
                    cursor.execute(query, (airline_key,))
                flights = cursor.fetchall()
            else:
                flight_error = "No airline reference column found in flight table."
        except Exception as e:
            flight_error = str(e)

        try:
            pilot_columns = get_table_columns(cursor, "pilot_aircraft")
            pilot_airline_col = first_existing_column(
                pilot_columns, ["airline_id", "airlineid", "airline", "airline_code", "airline_name"]
            )
            pilot_available_col = first_existing_column(
                pilot_columns, ["availability", "is_available", "available", "status"]
            )

            if pilot_airline_col:
                if pilot_available_col:
                    query = f"SELECT * FROM pilot_aircraft WHERE {pilot_airline_col} = %s AND LOWER(CAST({pilot_available_col} AS CHAR)) IN ('1', 'true', 'yes', 'available', 'active')"
                    cursor.execute(query, (airline_key,))
                else:
                    query = f"SELECT * FROM pilot_aircraft WHERE {pilot_airline_col} = %s"
                    cursor.execute(query, (airline_key,))
                pilots = cursor.fetchall()
            else:
                pilot_error = "No airline reference column found in pilot_aircraft table."
        except Exception as e:
            pilot_error = str(e)

        return render_template(
            'airline_info.html',
            airline=airline,
            flights=flights,
            pilots=pilots,
            flight_columns=list(flights[0].keys()) if flights else [],
            pilot_columns=list(pilots[0].keys()) if pilots else [],
            flight_error=flight_error,
            pilot_error=pilot_error
        )
    except Exception as e:
        return f"Database Error: {e}"
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)