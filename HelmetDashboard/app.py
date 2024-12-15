from flask import Flask, render_template, jsonify, request, session, redirect, url_for
import sqlite3
import matplotlib.pyplot as plt
from io import BytesIO
import pandas as pd
import subprocess
import base64  # Required for encoding chart images
from flask_cors import CORS

app = Flask(__name__)

# Sample user database (replace with a proper database or authentication mechanism)
users = {
    "admin": "admin123",
    "user": "admin"
}

# Path to the Excel file
EXCEL_FILE_PATH = "data/helmet_data.xlsx"

@app.route('/')
def home():
    # Redirect to the login page
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users and users[username] == password:
            # Redirect to index page on successful login
            return redirect(url_for('dashboard'))
        else:
            return "Invalid Credentials!", 401
    return render_template('login.html')

@app.route('/index')
def dashboard():
    try:
        # Load the Excel file and get the last row
        helmet_data = pd.read_excel(EXCEL_FILE_PATH)
        last_row = helmet_data.iloc[-1]
        helmet_status = last_row.get("helmet_worn", "No data available")  # Replace 'helmet_worn' with the actual column name
    except Exception as e:
        helmet_status = f"Error loading data: {e}"
    
    conn = connect_db()
    cursor = conn.cursor()

    # Fetch the latest 10 helmets (based on timestamp or rowid)
    cursor.execute("SELECT DISTINCT rowid, co_level, timestamp FROM sensor_data ORDER BY timestamp DESC LIMIT 10")
    helmets = cursor.fetchall()

    conn.close()

    # Generate a dummy list of helmets (1 to 10 for example purposes)
    helmets = [(i,) for i in range(1, 11)]
    active_helmet = helmets[0]  # Set the first helmet as active

    # Render the dashboard template with helmet data and the logged-in username
    return render_template('index.html', helmets=helmets, active_helmet=active_helmet)
    


# Start the helmet monitoring script as a subprocess
subprocess.Popen(["python", "helmet_status_monitor.py"])  # Adjust the path as needed

# Enable Cross-Origin Resource Sharing (CORS) for APIs
CORS(app)

# Database connection function
def connect_db():
    return sqlite3.connect('data/helmet_data.db')  # Use forward slashes for cross-platform compatibility

# Home route (Dashboard)
@app.route('/')
def index():
    conn = connect_db()
    cursor = conn.cursor()

    # Fetch the latest 10 helmets (based on timestamp or rowid)
    cursor.execute("SELECT DISTINCT rowid, co_level, timestamp FROM sensor_data ORDER BY timestamp DESC LIMIT 10")
    helmets = cursor.fetchall()

    conn.close()

    # Generate a dummy list of helmets (1 to 10 for example purposes)
    helmets = [(i,) for i in range(1, 11)]
    active_helmet = helmets[0]  # Set the first helmet as active

    # Render the dashboard template with helmet data and the logged-in username
    return render_template('index.html', helmets=helmets, active_helmet=active_helmet, username=session['username'])

# Helmet Detail Page (for active helmet)
@app.route('/helmet/<int:helmet_id>')
def helmet_detail(helmet_id):
    conn = connect_db()
    cursor = conn.cursor()

    # Fetch detailed data for the selected helmet
    cursor.execute("SELECT * FROM sensor_data WHERE rowid = ? ORDER BY timestamp DESC", (helmet_id,))
    rows = cursor.fetchall()

    # Generate chart for the specific helmet's data
    cursor.execute("SELECT timestamp, co_level FROM sensor_data WHERE rowid = ?", (helmet_id,))
    data = cursor.fetchall()

    timestamps, co_levels = zip(*data) if data else ([], [])
    plt.figure(figsize=(10, 5))
    plt.plot(timestamps, co_levels, marker='o')
    plt.title(f"CO Levels for Helmet {helmet_id}")
    plt.xlabel("Timestamp")
    plt.ylabel("CO Level")
    plt.xticks(rotation=45)
    plt.tight_layout()

    # Save plot to a BytesIO object and encode as base64
    img = BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode()

    conn.close()

    return render_template('helmet_detail.html', helmet_id=helmet_id, data=rows, plot_url=plot_url)


# Fetch real-time data for individual helmet view
@app.route('/get_helmet_data', methods=['GET'])
def get_helmet_data():
    data = pd.read_excel('data/helmet_data.xlsx')  # Use forward slashes
    data = data.dropna()
    data = data.tail(5)  # Keep the last 5 rows

    response = {
        'labels': data['timestamp'].astype(str).tolist(),
        'values': data['co_level'].tolist(),
    }
    return jsonify(response)


# Offline Helmets Page
@app.route('/offline-helmets')
def offline_helmets():
    return render_template('offline_helmets.html')

if __name__ == '__main__':
    app.run(debug=True)
    





