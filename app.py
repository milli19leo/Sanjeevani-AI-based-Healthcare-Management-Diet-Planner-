from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify,send_from_directory,send_file
import MySQLdb
import pymysql
import mysql.connector
import pymysql.cursors
from datetime import datetime, date  , timedelta
import google.generativeai as genai
from werkzeug.security import generate_password_hash, check_password_hash
import pickle
import requests
import os
import re
import pdfplumber
from reportlab.lib.pagesizes import letter, portrait
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from bs4 import BeautifulSoup
from io import BytesIO
import joblib
import pandas as pd
from werkzeug.utils import secure_filename
from google.cloud import documentai_v1 as documentai
import traceback

app = Flask(__name__)

app.config["SECRET_KEY"] = "your_strong_secret_key"
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_USE_SIGNER"] = True
app.config["SESSION_COOKIE_NAME"] = "my_secure_session"
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SECURE"] = False  
app.secret_key = 'your_secret_key'  
app.config['SESSION_TYPE'] = 'filesystem'  

DB_CONFIG = {
    'host': 'sanjeevani-rds.cn80mgk4e3ug.ap-south-1.rds.amazonaws.com',
    'user': 'admin',
    'password': 'mypassword',
    'db': 'health_db',  
    'cursorclass': pymysql.cursors.DictCursor,  
    'port':3306
}

def create_database_if_not_exists():
    try:
        conn = pymysql.connect(
            host=DB_CONFIG['host'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password']
        )
        cursor = conn.cursor()
        cursor.execute("CREATE DATABASE IF NOT EXISTS health_db")
        conn.commit()
        conn.close()
        print("✅ Database checked/created successfully.")
    except Exception as e:
        print("❌ Error creating database:", e)

def get_db_connection():
    try:
        conn = pymysql.connect(
            host=DB_CONFIG['host'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            db=DB_CONFIG['db'],
            cursorclass=DB_CONFIG['cursorclass'],
            port=DB_CONFIG['port']
        )
        return conn
    except pymysql.MySQLError as e:
        print("Error connecting to the database:", e)
        return None 
    
def create_tables():
    conn = get_db_connection()
    cursor = conn.cursor()


    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS admin(
        admin_id INT AUTO_INCREMENT PRIMARY KEY,
        email VARCHAR(255) UNIQUE NOT NULL,
        password VARCHAR(255) NOT NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS selected_doctors(
        id INT NOT NULL AUTO_INCREMENT,
        user_id VARCHAR(50) NOT NULL,
        name VARCHAR(255) NOT NULL,
        address TEXT NOT NULL,
        rating DECIMAL(3,1),
        PRIMARY KEY (id),
        KEY (user_id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reports(
        id INT NOT NULL AUTO_INCREMENT,
        user_id VARCHAR(50) NOT NULL,
        filename VARCHAR(255) NOT NULL,
        upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        filepath VARCHAR(255),
        PRIMARY KEY (id),
        UNIQUE (filename),
        KEY (user_id)
    )
    """)


    cursor.execute("""
    CREATE TABLE IF NOT EXISTS registration (
        user_id VARCHAR(20) PRIMARY KEY,
        full_name VARCHAR(255) NOT NULL,
        dob DATE NOT NULL,
        email VARCHAR(255) UNIQUE NOT NULL,
        password VARCHAR(255) NOT NULL
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS profile (
        user_id VARCHAR(20) PRIMARY KEY,
        full_name VARCHAR(255) NOT NULL,
        age INT NOT NULL,
        gender ENUM('Male', 'Female', 'Other') NOT NULL,
        height INT NOT NULL,
        weight INT NOT NULL,
        city VARCHAR(100) NOT NULL,
        state VARCHAR(100) NOT NULL,
        FOREIGN KEY (user_id) REFERENCES registration(user_id) ON DELETE CASCADE
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sessions (
        session_id VARCHAR(255) NOT NULL PRIMARY KEY,
        data LONGBLOB NOT NULL,
        expiry TIMESTAMP NOT NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS diet_reports (
        report_id INT AUTO_INCREMENT PRIMARY KEY,
        user_id VARCHAR(50) NOT NULL,
        filename VARCHAR(255) NOT NULL,
        upload_time DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES registration(user_id) ON DELETE CASCADE
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS diet (
        diet_id INT AUTO_INCREMENT PRIMARY KEY,
        user_id VARCHAR(50) NOT NULL,
        food_preference VARCHAR(255) NOT NULL,
        activity_level VARCHAR(255) NOT NULL,
        disease VARCHAR(255) NOT NULL DEFAULT 'None',
        FOREIGN KEY (user_id) REFERENCES registration(user_id) ON DELETE CASCADE
    )
    """)
    
    conn.commit()
    conn.close()

create_tables()

def save_session_to_db(session_id, data):
    conn = get_db_connection()
    cursor = conn.cursor()

    expiry = datetime.now() + timedelta(days=1)  
    pickled_data = pickle.dumps(data)  

    query = """INSERT INTO sessions (session_id, data, expiry)
               VALUES (%s, %s, %s)
               ON DUPLICATE KEY UPDATE data = %s, expiry = %s"""

    cursor.execute(query, (session_id, pickled_data, expiry, pickled_data, expiry))
    conn.commit()
    conn.close()

def load_session_from_db(session_id):
    conn = mysql.connector.connect(host="sanjeevani-rds.cn80mgk4e3ug.ap-south-1.rds.amazonaws.com", user="admin", password="mypassword", database="health")
    cursor = conn.cursor()

    cursor.execute("SELECT data FROM sessions WHERE session_id = %s", (session_id,))
    result = cursor.fetchone()

    cursor.close()
    conn.close()

    if result:  
        return result[0]  
    return None  

@app.before_request
def before_request():
    session_id = request.cookies.get("session_id")  
    if session_id:
        session_data = load_session_from_db(session_id)
    else:
        session_data = None  

@app.after_request
def after_request(response):
    session_id = session.get('session_id')
    if not session_id:
        session_id = str(datetime.now().timestamp())
        session['session_id'] = session_id  

    save_session_to_db(session_id, dict(session)) 
    response.set_cookie("session_id", session_id, httponly=True, samesite='Lax')
    return response

@app.route('/set_session')
def set_session():
    session["user_id"] = "USER12345"
    session["full_name"] = "John Doe"
    return "Session Set!"

@app.route('/get_session')
def get_session():
    return f"User ID: {session.get('user_id')}, Name: {session.get('full_name')}"

@app.route('/logout', methods=['POST'])
def logout():
    session.clear()  
    return redirect('/login')


def generate_user_id(full_name, dob):
    name_part = full_name[:4].upper()
    dob_part = dob.replace('-', '')
    return f"{name_part}{dob_part}"

def calculate_age(dob):
    if isinstance(dob, date):
        birth_date = dob
    else:
        birth_date = datetime.strptime(dob, "%Y-%m-%d").date()
    
    today = date.today()
    return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))

@app.route('/')
def register_page():
    return render_template('register.html')

@app.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"success": False, "message": "Invalid JSON data"}), 400

        full_name = data.get('full_name')
        dob = data.get('dob')
        email = data.get('email')
        password = data.get('password')

        if not all([full_name, dob, email, password]):
            return jsonify({"success": False, "message": "All fields are required"}), 400

        user_id = generate_user_id(full_name, dob)
        password_hash = generate_password_hash(password)

        conn = get_db_connection()
        cursor = conn.cursor()

        query = """INSERT INTO registration (user_id, full_name, dob, email, password)
                   VALUES (%s, %s, %s, %s, %s)"""
        cursor.execute(query, (user_id, full_name, dob, email, password_hash))
        conn.commit()
        conn.close()

        session.clear()
        session['user_id'] = user_id
        session['full_name'] = full_name
        session['email'] = email

        return jsonify({"success": True, "message": "Registration successful!", "redirect": url_for('profile')})

    except mysql.connector.Error as err:
        return jsonify({"success": False, "message": f"Database error: {str(err)}"}), 500
    except Exception as e:
        return jsonify({"success": False, "message": f"Server error: {str(e)}"}), 500

@app.route('/login')
def login_page():
    """Render the registration page."""
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    print("Received request with headers:", request.headers)  
    print("Request method:", request.method)  

    if request.headers.get("Content-Type") != "application/json":
        return jsonify({"success": False, "message": "Content-Type must be application/json"}), 415

    try:
        data = request.get_json(silent=True) 
        print("Received request data:", data)  

        if not data:
            return jsonify({"success": False, "message": "Invalid JSON or empty request body"}), 400

        email = data.get("email")
        password = data.get("password")

        if not email or not password:
            return jsonify({"success": False, "message": "Email and password are required"}), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, full_name, password FROM registration WHERE email = %s", (email,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user["password"], password):
            session.clear()
            session["user_id"] = user["user_id"]
            session["full_name"] = user["full_name"]  

            print("DEBUG: Session data after login:", session)  
            print("Session user_id:", session.get("user_id"))

            return jsonify({
    "success": True, 
    "message": "Login successful!", 
    "redirect": url_for('home'),
    "user_id": user["user_id"], 
    "full_name": user["full_name"]
})


        return jsonify({"success": False, "message": "Invalid email or password"}), 400
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/profile')
def profile():
    user_id = session.get('user_id')
    full_name = session.get('full_name')  

    if not user_id:
        flash("Please log in first.", "warning")
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT dob FROM registration WHERE user_id = %s", (user_id,))
    user_data = cursor.fetchone()

    if not user_data:
        flash("User not found.", "danger")
        return redirect(url_for('login'))

    user_data['full_name'] = full_name  
    user_data['age'] = calculate_age(user_data['dob'])

    cursor.execute("SELECT * FROM profile WHERE user_id = %s", (user_id,))
    profile = cursor.fetchone()
    conn.close()

    return render_template('profile.html', user=user_data, profile=profile)

@app.route('/update_profile', methods=['POST'])
def update_profile():
    if request.content_type != 'application/json':
        return jsonify({"success": False, "message": "Content-Type must be application/json"}), 415

    data = request.get_json()
    if not data:
        return jsonify({"success": False, "message": "Invalid JSON data"}), 400

    user_id = session.get('user_id') 
    if not user_id:
        return jsonify({"success": False, "message": "User not logged in"}), 401

    gender = data.get('gender')
    height = data.get('height')
    weight = data.get('weight')
    city = data.get('city')
    state = data.get('state')

    if not all([gender, height, weight, city, state]):
        return jsonify({"success": False, "message": "Missing required fields"}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        query = """
        INSERT INTO profile (user_id, full_name, age, gender, height, weight, city, state)
        SELECT 
            r.user_id, 
            r.full_name, 
            TIMESTAMPDIFF(YEAR, r.dob, CURDATE()) AS age, 
            %s, %s, %s, %s, %s
        FROM registration r
        WHERE r.user_id = %s
        ON DUPLICATE KEY UPDATE 
            gender = VALUES(gender),
            height = VALUES(height),
            weight = VALUES(weight),
            city = VALUES(city),
            state = VALUES(state);
        """
        cursor.execute(query, (gender, height, weight, city, state, user_id))
        conn.commit()
        conn.close()

        return jsonify({"success": True, "message": "Profile updated successfully!", "redirect": url_for('login')})

    except mysql.connector.Error as e:
        return jsonify({"success": False, "message": f"Database error: {str(e)}"}), 500

def get_user_profile(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, full_name, age, gender, height, weight, city, state FROM profile WHERE user_id = %s", (user_id,))
    user = cursor.fetchone()
    cursor.close()
    return user

@app.route('/get_profile')
def get_profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    user = get_user_profile(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404

    return jsonify(user)

@app.route('/home')
def home():
    """Render the registration page."""
    return render_template('index.html')

@app.route('/profileDB')
def profileDB():
    return render_template('profileDB.html')

@app.route('/create_admin')
def create_admin():
    conn = get_db_connection()
    cursor = conn.cursor()

    try:

        admin_email = "adminadmin@gmail.com"
        admin_password = "admin1234"

        cursor.execute("SELECT * FROM admin WHERE email = %s", (admin_email,))
        existing_admin = cursor.fetchone()

        if existing_admin:
            return "Admin already exists!"

        hashed_password = generate_password_hash(admin_password)
        cursor.execute("INSERT INTO admin (email, password) VALUES (%s, %s)", 
                       (admin_email, hashed_password))
        conn.commit()
        conn.close()

        return "Admin inserted successfully!"
    except Exception as e:
        print("Error inserting admin:", e)
        return f"Error: {e}"



@app.route('/admin_login')
def admin_login_page():
    return render_template('admin_login.html')

@app.route('/admin_login', methods=['POST'])
def admin_login():
    try:
        data = request.json
        email = data.get("email")
        password = data.get("password")
        print("Received login attempt:", email)

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM admin WHERE email = %s", (email,))
        admin = cursor.fetchone()
        print("DB response:", admin)

        if admin and check_password_hash(admin['password'], password):
            return jsonify({"success": True, "message": "Login successful", "redirect": "/admin"})
        else:
            return jsonify({"success": False, "message": "Invalid email or password"}), 401

    except Exception as e:
        import traceback
        print("Login error:", e)
        traceback.print_exc()
        return jsonify({"success": False, "message": "Internal server error"}), 500

    finally:
        cursor.close()
        conn.close()
    

@app.route('/uploads/<path:filename>')
def handle_upload_file(filename):

    uploads_dir = os.path.join(app.root_path, 'uploads')
    return send_from_directory(uploads_dir, filename)

@app.route('/admin')
def admin_panel():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT user_id, filepath, filename FROM reports")
        report_rows = cursor.fetchall()
        print("Fetched report rows:", report_rows)

        user_reports = []

        for report in report_rows:
            user_id = report['user_id']
            filepath = os.path.basename(report['filepath'])
            filename = report['filename']

            cursor.execute("""
                SELECT full_name AS name, age, height, weight, city, state, gender 
                FROM profile 
                WHERE user_id = %s
            """, (user_id,))
            profile = cursor.fetchone()
            print(f"Profile for {user_id}:", profile)

            if profile:
                user_reports.append({
                    "user_id": user_id,
                    "name": profile["name"],
                    "age": profile["age"],
                    "height": profile["height"],
                    "weight": profile["weight"],
                    "city": profile["city"],
                    "state": profile["state"],
                    "gender": profile["gender"],
                    "filepath": filepath,
                    "file_name": filename
                })

        print("Final user_reports list:", user_reports)
        return render_template("admin.html", reports=user_reports)  

    except Exception as e:
        import traceback
        print("Error in /admin route:", e)
        traceback.print_exc()  
        return "Internal Server Error", 500
    



#EHR============================================================================================================================================
# Routes
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {"pdf", "png", "jpg", "jpeg"}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/ehr')
def ehr():
    return render_template('ehr.html')

@app.route('/ehr/doctor', methods=['GET', 'POST'])
def ehr_doctor():
    return render_template('ehr_doctors.html')

@app.route('/ehr/doctors')
def ehr_doctors():
    user_id = session.get('user_id')  
    if not user_id:
        return redirect(url_for('login'))  
    
    conn = get_db_connection()
    
    cursor.execute("SELECT name, address, rating FROM selected_doctors WHERE user_id = %s ORDER BY rating DESC", (user_id,))
    doctors = cursor.fetchall()
    
    return render_template('ehr_doctors.html', doctors=doctors)


@app.route('/get_uploaded_reports')
def get_uploaded_reports():
    user_id = session.get('user_id')  
    if not user_id:
        return jsonify({"success": False, "message": "User not logged in"}), 401

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT filename FROM reports WHERE user_id = %s ORDER BY upload_time DESC", (user_id,))
        files = cursor.fetchall()

        conn.close()
        return jsonify({"success": True, "files": files})

    except pymysql.MySQLError as e:
        return jsonify({"success": False, "message": f"Database error: {str(e)}"}), 500
    
@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"success": False, "message": "No file part"})

    file = request.files["file"]
    if file.filename == "" or not allowed_file(file.filename):
        return jsonify({"success": False, "message": "Invalid file"})

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(filepath)
    
    conn = get_db_connection()
    with conn.cursor() as cursor:
        try:
            cursor.execute("INSERT INTO reports (user_id, filename, filepath, upload_time) VALUES (%s, %s, %s, NOW())", (session['user_id'], filename, filepath))
            conn.commit()
            return jsonify({"success": True, "message": "File uploaded successfully."})
        except pymysql.MySQLError as e:
            conn.rollback()
            return jsonify({"success": False, "message": f"Database error: {str(e)}"})
        finally:
            conn.close()

@app.route('/ehr/reports')
def ehr_reports():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("SELECT filename FROM reports WHERE user_id = %s ORDER BY upload_time DESC", (user_id,))
        files = cursor.fetchall()
    conn.close()
    
    return render_template('ehr_report.html', files=files)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

@app.route('/delete-file', methods=['DELETE'])
def delete_file():
    data = request.get_json()
    filename = data.get('filename')
    if not filename:
        return jsonify({"success": False, "message": "Filename missing"}), 400
    
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    conn = get_db_connection()
    with conn.cursor() as cursor:
        try:
            cursor.execute("DELETE FROM reports WHERE filename = %s", (filename,))
            conn.commit()
            if os.path.exists(file_path):
                os.remove(file_path)
            return jsonify({"success": True, "message": "File deleted successfully"})
        except pymysql.MySQLError as e:
            conn.rollback()
            return jsonify({"success": False, "message": f"Database error: {str(e)}"}), 500
        finally:
            conn.close()

@app.route('/ehr/diet')
def ehr_diet():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT filename FROM diet_reports WHERE user_id = %s ORDER BY upload_time DESC LIMIT 1
    """, (user_id,))
    result = cursor.fetchone()
    conn.close()

    if not result or not result.get('filename'):
        return render_template("ehr_diet.html", table_data=None)

    latest_pdf_path = os.path.join(UPLOAD_FOLDER, result['filename'])
    table_data = []

    try:
        with pdfplumber.open(latest_pdf_path) as pdf:
            for page in pdf.pages:
                extracted_table = page.extract_table()
                if extracted_table:
                    for row in extracted_table:
                        table_data.append(row)
    except Exception as e:
        return f"Error extracting table from PDF: {str(e)}"

    return render_template("ehr_diet.html", table_data=table_data)

@app.route('/ehr/report')
def ehr_report():
    return render_template('ehr_report.html')

#Diet========================================================================================================================================
basic_prompt="I need it completely in html with styling.The data should be in white font color with quantity how much needs to be consumed should be written. Don't show any background color.There should be no suggestions and other information. Also don't include note or any extra information.The food nutrients should be displayed in a table format without background color and heading should be in white font color and bold in the left of the meal plan.The food nutrients should be in another table. Don't include tofu and provide diet according to age given. " 

my_api_key_gemini = "AIzaSyBWO2wo3W8jmaZ3ajUKAt8LOnYxxkldtso"  
genai.configure(api_key=my_api_key_gemini)

UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'diet_records')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)  

@app.route('/diet')
def diet():
    return render_template('diet.html')

def fetch_user_profile(user_id):
    if not user_id:
        return None
    
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT r.user_id, r.dob, p.height, p.weight, p.state, d.food_preference, d.activity_level, d.disease
    FROM registration r
    JOIN profile p ON r.user_id = p.user_id
    JOIN diet d ON r.user_id = d.user_id
    """)

    
    profile = cursor.fetchone()
    conn.close()
    
    print("🔍 Debug: Fetched profile from DB:", profile)  

    if profile and all(profile.values()):
        age = calculate_age(profile['dob'])
        return age, profile['height'], profile['weight'], profile['state'], profile['food_preference'], profile['activity_level'], profile['disease']
   
    print("❌ Error: Missing data in profile") 
    return None


def calculate_age(dob):
    birth_date = datetime.strptime(str(dob), "%Y-%m-%d")
    today = datetime.today()
    return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))

def calculate_bmi(weight, height):
    return weight / ((height / 100) ** 2)

def generate_meal_plan(bmi, state, age, food_preference, activity_level,disease):
    if bmi < 18.5:
        prompt = f"Create a weekly meal plan featuring high-calorie Indian dishes for a {food_preference} person of {age} from {state} who is underweight with {disease if disease else 'no specific disease'}. Consider their BMI ({bmi}) and activity level ({activity_level}). Include breakfast, lunch, and dinner options.{basic_prompt}"
    elif 18.5 <= bmi < 24.9:
        prompt = f"Generate a balanced weekly meal plan featuring traditional Indian dishes for a {food_preference} person of {age} from {state} with a normal weight with {disease if disease else 'no specific disease'}. Consider their BMI ({bmi}) and activity level ({activity_level}). Include healthy recipes for breakfast, lunch, and dinner.{basic_prompt}"
    elif 25 <= bmi < 29.9:
        prompt = f"Suggest a weekly meal plan for a {food_preference} person of {age} from {state} who is overweight with {disease if disease else 'no specific disease'}. Consider their BMI ({bmi}) and activity level ({activity_level}). Include low-calorie Indian dishes for breakfast, lunch, and dinner.{basic_prompt}"
    else:
        prompt = f"Outline a weekly meal plan for a {food_preference} person of {age} from {state} who is obese with {disease if disease else 'no specific disease'}. Consider their BMI ({bmi}) and activity level ({activity_level}). Include low-sugar and low-calorie Indian recipes for breakfast, lunch, and dinner.{basic_prompt}"

    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content(prompt)
    return response.text.replace("```pdf","").replace("```","")

@app.route('/get_user_id', methods=['GET'])
def get_user_id():
    if 'user_id' in session:
        return jsonify({"user_id": session['user_id']})
    return jsonify({"error": "User not logged in"}), 401


@app.route('/diet_plan', methods=['GET', 'POST'])
def diet_plan():
    if 'user_id' not in session:
        return redirect(url_for('login'))  

    user_id = session['user_id']
    profile = fetch_user_profile(user_id)
    if not profile:
        return "Error: User profile data is incomplete", 400

    age, height, weight, state, food_preference, activity_level,disease = profile
    bmi = calculate_bmi(weight, height)
    meal_plan = generate_meal_plan(bmi, state, age, food_preference, activity_level,disease)

    return render_template('result.html', food_preference=food_preference, activity_level=activity_level , disease=disease, meal_plan=meal_plan, bmi=bmi)

@app.route('/save_diet', methods=['POST'])
def save_diet():
    if 'user_id' not in session:
        return jsonify({"success": False, "message": "User not logged in"}), 401

    user_id = session['user_id']
    food_preference = request.form.get('food_preference')
    activity_level = request.form.get('activity_level')
    disease = request.form.get('disease', 'None')  

    print(f"🔍 Debug: user_id={user_id}, food_preference={food_preference}, activity_level={activity_level}, disease={disease}")

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO diet (user_id, food_preference, activity_level, disease)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE food_preference=%s, activity_level=%s, disease=%s
        """, (user_id, food_preference, activity_level, disease, food_preference, activity_level, disease))

        conn.commit()
        conn.close()

        return jsonify({"success": True, "user_id": user_id})

    except mysql.connector.Error as err:
        print(f"❌ Database Error: {err}") 
        return jsonify({"success": False, "message": f"Database error: {err}"}), 500

def extract_table_from_html(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    table_data = []
    for row in soup.find_all("tr"):
        cells = [Paragraph(cell.get_text(strip=True), getSampleStyleSheet()["BodyText"]) for cell in row.find_all(["th", "td"])]
        if cells:
            table_data.append(cells)
    return table_data

@app.route('/generate_diet_pdf', methods=['POST'])
def generate_diet_pdf():
    """Generates a PDF from meal plan HTML and sends it as a buffer to the client."""
    try:
        data = request.get_json()
        meal_plan_html = data.get("meal_plan")
        bmi = data.get("bmi")

        if not meal_plan_html:
            print("❌ No meal plan provided")
            return jsonify({"success": False, "message": "No meal plan provided"}), 400

        user_id = session['user_id']  

        meal_plan_table = extract_table_from_html(meal_plan_html)
        if not meal_plan_table:
            print("❌ Invalid table format in meal plan")
            return jsonify({"success": False, "message": "Invalid table format"}), 400

        print("✅ Generating PDF in memory...")

        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=portrait(letter))
        elements = [
            Paragraph("Your Diet Plan", getSampleStyleSheet()["Title"]),
            Paragraph(f"BMI: {bmi}", getSampleStyleSheet()["Normal"]),
            Spacer(1, 12)
        ]
        table = Table(meal_plan_table)
        table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey)
        ]))
        elements.append(table)
        doc.build(elements)

        buffer.seek(0)

        print("✅ Sending PDF buffer to client...")

        filename = f"diet_plan_{int(datetime.now().timestamp())}.pdf"
        filepath = os.path.join(UPLOAD_FOLDER, filename)

        with open(filepath, "wb") as f:
            f.write(buffer.getbuffer())

        print(f"✅ PDF saved at {filepath}")

        upload_time = datetime.now()
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO diet_reports (user_id, filename, upload_time) VALUES (%s, %s, %s)",
                (user_id, filename, upload_time)
            )
            conn.commit()
            conn.close()
            print(f"✅ PDF record inserted: {filename}")
        except mysql.connector.Error as err:
            print(f"❌ Database Error: {err}")
            return jsonify({"success": False, "message": "Database error"}), 500

        buffer.seek(0)
        return send_file(
            buffer,
            as_attachment=True,
            download_name=filename,
            mimetype="application/pdf"
        )

    except Exception as e:
        print(f"❌ Exception in PDF generation: {e}")
        return jsonify({"success": False, "message": str(e)}), 500



@app.route('/download_diet_pdf/<filename>')
def download_diet_pdf(filename):
    """Handles the PDF download."""
    filepath = os.path.join(UPLOAD_FOLDER, filename)

    if not os.path.exists(filepath):
        print(f"❌ File not found: {filepath}")
        return "Error: File not found", 404

    return send_file(filepath, as_attachment=True)

@app.route('/diet_reports')
def diet_reports():
    """Fetches all diet reports from the database."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, filename, upload_time FROM diet_reports ORDER BY upload_time DESC")
        reports = cursor.fetchall()
        conn.close()
    except mysql.connector.Error as err:
        print(f"❌ Database Error: {err}")
        return jsonify({"success": False, "message": "Database error"}), 500

    return jsonify({"success": True, "reports": reports})


#DOCTOR========================================================================================================================================
@app.route('/find_doctor')
def doctor():
    return render_template('index3.html')

def fetch_doctors(city, specialty, api_key):
    query = f"{specialty} in {city}"
    url = f"https://maps.googleapis.com/maps/api/place/textsearch/json?query={query}&key={api_key}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return [
            {
                "name": place.get("name"),
                "address": place.get("formatted_address"),
                "rating": float(place.get("rating")) if place.get("rating") is not None else None,
            }
            for place in data.get("results", [])
        ]
    return None


db = get_db_connection()
cursor = db.cursor()

@app.route('/save_selected', methods=['POST'])
def save_selected():
    if 'user_id' not in session:
        return "User not logged in", 403  

    user_id = session['user_id']
    selected_doctors = request.form.getlist('selected_doctors')

    if not selected_doctors:
        return "No doctors selected", 400

    try:
        for doc_index in selected_doctors:
            name = request.form.get(f'name_{doc_index}')
            address = request.form.get(f'address_{doc_index}')
            rating = request.form.get(f'rating_{doc_index}')

            sql = "INSERT INTO selected_doctors (user_id, name, address, rating) VALUES (%s, %s, %s, %s)"
            cursor.execute(sql, (user_id, name, address, rating))

        db.commit()
        return "Doctors saved successfully", 200

    except MySQLdb.Error as e:
        db.rollback()
        return f"Error saving data: {str(e)}", 500

@app.route('/index2.html', methods=['GET'])
def find_doctors():
    city = request.args.get('city')
    specialty = request.args.get('specialty')
    api_key = "AIzaSyBSzQDWcv889gBErlt2QbjsNP-laF2aJ4E" 

    if not city or not specialty:
        return render_template('index2.html', error="City and Specialty are required", doctors=None)

    doctors = fetch_doctors(city, specialty, api_key)
    if doctors is None:
        return render_template('index2.html', error="Error fetching data from the Google API", doctors=None)

    return render_template('index2.html', city=city, specialty=specialty, doctors=doctors)

def process_document(project_id, location, processor_id, file_path):
    """Processes a document using the Document AI API and returns extracted entities."""

    client = documentai.DocumentProcessorServiceClient()
    name = f"projects/{project_id}/locations/{location}/processors/{processor_id}"

    with open(file_path, "rb") as f:
        raw_document = documentai.RawDocument(content=f.read(), mime_type="image/jpeg")

    request = documentai.ProcessRequest(name=name, raw_document=raw_document)

    result = client.process_document(request=request)
    document = result.document

    entities = []
    if document:
        for entity in document.entities:
            entities.append({"type": entity.type_, "value": entity.mention_text})
    return entities

try:
    with open("random_forest_model.pkl", "rb") as model_file:
        model = pickle.load(model_file)

    with open("label_encoder.pkl", "rb") as encoder_file:
        label_encoder = pickle.load(encoder_file)

    with open("scaler.pkl", "rb") as scaler_file:
        scaler = pickle.load(scaler_file)

    column_names = pd.read_csv("Final_Updated_Dataset_Cleaned_Shuffled.csv").drop(columns=['Disease', 'ID'] if 'ID' in pd.read_csv("Final_Updated_Dataset_Cleaned_Shuffled.csv").columns else ['Disease']).columns.tolist()

except FileNotFoundError as e:
    print(f"Error loading model files: {e}. Please ensure the model files and CSV are in the same directory as app.py.")
    exit(1)

@app.route("/prediction", methods=["GET", "POST"])
def prediction():
    extracted_entities = []
    prediction = None

    if request.method == "POST":
        if "file" in request.files:
            file = request.files["file"]
            if file.filename != "":
                file.save("uploaded_file.jpg")
                project_id = "key-fabric-447217-n3"
                location = "us"
                processor_id = "d9b98ec4ba77b1bd"
                extracted_entities = process_document(project_id, location, processor_id, "uploaded_file.jpg")
                os.remove("uploaded_file.jpg")

                input_data = {}
                for entity in extracted_entities:
                    type_ = entity['type']
                    value_ = entity['value']

                    value_ = re.sub(r'[^\d.]', '', value_)  
                    value_ = value_.replace(',', '')  

                    if type_ in column_names:
                        try:
                            input_data[type_] = float(value_)
                        except ValueError:
                            print(f"Warning: Could not convert '{value_}' to float for type '{type_}'.")
                            pass  

                if all(col in input_data for col in column_names):
                    input_list = [input_data[col] for col in column_names]
                    input_df = pd.DataFrame([input_list], columns=column_names)
                    scaled_input = scaler.transform(input_df)
                    prediction_encoded = model.predict(scaled_input)[0]
                    prediction = label_encoder.inverse_transform([prediction_encoded])[0]

                else:
                    prediction = "Missing required data for prediction."

        else:
            return "No file part"

    return render_template("prediction.html", entities=extracted_entities, prediction=prediction)

@app.route('/feedback')
def feedback():
    print("Feedback route hit")
    return render_template('feedback.html')

if __name__ == "__main__":
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "document_ai.json"
    app.run(debug=True)




