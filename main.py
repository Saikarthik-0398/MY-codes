from flask import Flask, request, render_template, redirect, url_for,session,g
import pymysql
import fitz
import re
import pandas
import json
from datetime import datetime
current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
import joblib
from joblib import load
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import load_model
from werkzeug.utils import secure_filename
import os
from flask import send_file
from docx import Document
import docx
import io
import base64
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
import ast
from docx.shared import Pt, RGBColor
import smtplib
from email.message import EmailMessage
from collections import defaultdict
from datetime import datetime
import re
import json
import cgi
import urllib.parse
import os
import smtplib
from email.message import EmailMessage
import pickle
import joblib
import matplotlib.pyplot as plt
import io
import base64
import pandas as pd
import matplotlib
from datetime import timedelta


app = Flask(__name__)
app.secret_key = "gitamuniversity"  
app.permanent_session_lifetime = timedelta(minutes=30)  # Set session timeout to 30 minutes

connection = pymysql.connect(
    host='127.0.0.1',
    user='root',
    password='',
)

current =""
cursor = connection.cursor()
cursor.execute('''use patient;''')

clr = load("random_forest_model.joblib")
scaler = load("scaler.joblib")
labelencoder = load("label_encoder.joblib")

model = joblib.load("lunggimodel.pkl")
label_encoder = joblib.load("lunggilabel.pkl")
Scaler = joblib.load("lunggiscaler.pkl")



@app.before_request
def make_session_permanent():
    session.permanent = True  

@app.route("/advance")
def adv():
    cursor.execute(f'''select type from alldoc where mail="{session["user"]}";''')
    dat = cursor.fetchone()[0]
    if(dat=='blood'):
        return render_template("bloodadvanced.html")
    elif(dat=='skin'):
        return render_template("skinadvanced.html")
    elif(dat=='lung'):
        return render_template("lungadvanced.html")
    else:
        return render_template("advanced.html")

def preprocess_image(image_path):
    image = tf.keras.preprocessing.image.load_img(image_path, target_size=(128, 128))  # Resize the image
    image = tf.keras.preprocessing.image.img_to_array(image)  # Convert to numpy array
    image = image / 255.0  # Normalize
    image = tf.expand_dims(image, axis=0)  # Add batch dimension
    return image



@app.route("/new", methods=['POST'])
def fun2():
    user = request.form.get("name")  
    email = request.form.get("email")
    pas = request.form.get("password")
    typ = request.form.get("type")
    cursor.execute(f'''SELECT email FROM doctor WHERE email="{email}";''')
    dat = cursor.fetchone()
    print(f"Checking for email: {email}, Result: {dat}")  
    
    if(dat):
        return "Account already exists"
    else:
        cursor.execute(f'''INSERT INTO doctor VALUES("{user}", "{email}", "{pas}");''')
        connection.commit()
        cursor.execute(f'''INSERT INTO alldoc VALUES("{email}", "{user}", "{typ}");''')
        connection.commit()
        return "account_created" 


@app.route("/login", methods=['POST', 'GET'])
def fun1():
    user = request.form.get("email")  
    session["user"] = user
    pas = request.form.get("password")
    cursor.execute(f'''select email,password from doctor where email="{user}";''')
    dat = cursor.fetchone()
    if(dat is None):
        return "not_found"
    else:
        user1, pas1 = dat
        if(user1 == user and pas == pas1):
            return render_template("homePage.html")
        else:
            return "invalid"

@app.route("/home", methods=['GET'])
def home():
    return render_template("homepage.html")

@app.route("/")
def fun():
    return render_template("loginPage.html")

@app.route("/treat")
def fun3():
    connection.commit()
    cursor.execute('''SELECT name, type FROM alldoc WHERE mail = %s;''', (session["user"],))
    dat = cursor.fetchone()
    if not dat:
        return "Doctor not found.", 404
    name, typ = dat

    # Fetch appointments with patient names
    cursor.execute('''
        SELECT appointments.doctor_name, appointments.date, appointments.time, appointments.patient, details.name 
        FROM appointments 
        JOIN details ON appointments.patient = details.email 
        WHERE appointments.doctor_name = %s 
        ORDER BY appointments.date, appointments.time;
    ''', (name,))
    appointments = cursor.fetchall()

    # Group appointments by date
    grouped_appointments = defaultdict(list)
    for appointment in appointments:
        date = appointment[1].strftime('%Y-%m-%d')  # Format date as string
        grouped_appointments[date].append(appointment)

    return render_template("doctor_interface.html", cancertype=typ, grouped_appointments=grouped_appointments)

@app.route("/chatme")
def fun4():
    cursor.execute(f'''select name from alldoc where mail="{session["user"]}";''')
    dat = cursor.fetchone()[0]
    cursor.execute('''
        SELECT details.name,appointments.patient
        FROM appointments 
        JOIN details ON appointments.patient = details.email 
        WHERE appointments.doctor_name = %s 
        ORDER BY appointments.date, appointments.time;
    ''', (dat,))
    appointments = cursor.fetchall()
    return render_template("appointments.html", appointments=appointments)


@app.route("/chat")
def fun5():
    patient = request.args.get("mail")
    return redirect(f"http://127.0.0.1:5002/?user_id={patient}")


@app.route("/receiv")
def fun6():
    mail = request.args.get("email")
    session["patient"] = mail
    filename = f"C:/Users/saikarthik/Desktop/New Patient/patient_data/{mail}.txt"
    if(os.path.exists(filename)):
        f=open(filename)
        patdict=eval(f.read())
        return render_template("initreport.html",data=patdict)
    return "not found"

@app.route("/about")
def fun25():
    return render_template("about_us.html")    

BASE_DIR2 = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER2 = os.path.join(BASE_DIR2, "UPLOAD_FOLDER2")
app.config['UPLOAD_FOLDER2'] = UPLOAD_FOLDER2
if not os.path.exists(app.config['UPLOAD_FOLDER2']):
    os.makedirs(app.config['UPLOAD_FOLDER2'])
MODEL_PATH2 = os.path.join(BASE_DIR2, "skinmodel.h5")
loaded_model2 = load_model(MODEL_PATH2)


@app.route('/skinhome', methods=['GET', 'POST'])
def upload_filerse():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part in the request.')
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            flash('No selected file.')
            return redirect(request.url)
        
        if file:
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER2'], filename)
            file.save(filepath)
            
            # Preprocess image and make a prediction
            image_data = preprocess_image(filepath)
            prediction = loaded_model2.predict(image_data)
            predicted_class_index = prediction.argmax()  # Get the index of the highest probability
            conditions_data = {
    0: {
        "name": "Acne",
        "medicines": ["Benzoyl Peroxide", "Salicylic Acid", "Topical Retinoids"],
        "recommendations": [
            "Use non-comedogenic skincare products",
            "Avoid touching or picking at your skin",
            "Wash your face twice daily wit a mild cleanser"
        ],
        "expected_cure_time": "4-6 weeks with consistent treatment"
    },
    1: {
        "name": "Actinic Keratosis",
        "medicines": ["5-Fluorouracil Cream", "Imiquimod", "Cryotherapy"],
        "recommendations": [
            "Limit sun exposure",
            "Wear protective clothing",
            "Use broad-spectrum sunscreen daily"
        ],
        "expected_cure_time": "Depends on the severity, consult a dermatologist"
    },
    2: {
        "name": "Basal cell carcinoma",
        "medicines": ["Surgical Removal", "Topical Imiquimod", "Radiation Therapy (if advised)"],
        "recommendations": [
            "Regular skin check-ups",
            "Protect skin from UV radiation",
            "Follow up with a dermatologist"
        ],
        "expected_cure_time": "Varies; consult a healthcare provider for personalized treatment"
    },
    3: {
        "name": "Dermatofibroma",
        "medicines": ["No specific medication; often benign"],
        "recommendations": [
            "Avoid trauma to the affected area",
            "Monitor for changes in size or color",
            "Consult a dermatologist if necessary"
        ],
        "expected_cure_time": "Usually does not require treatment"
    },
    4: {
        "name": "Dry skin",
        "medicines": ["Moisturizers with Hyaluronic Acid", "Hydrating Creams with Ceramides", "Gentle emollients"],
        "recommendations": [
            "Avoid hot showers and harsh soaps",
            "Use a humidifier in dry environments",
            "Apply moisturizers immediately after bathing"
        ],
        "expected_cure_time": "Improves within days to weeks with proper care"
    },
    5: {
        "name": "Melanoma",
        "medicines": ["Targeted Therapy", "Immunotherapy", "Immediate oncologist consultation"],
        "recommendations": [
            "Seek urgent medical care",
            "Protect skin from further sun damage",
            "Adhere to treatment plans"
        ],
        "expected_cure_time": "Depends on the stage; early detection improves outcomes"
    },
    6: {
        "name": "Nevus",
        "medicines": ["No medication required for benign cases"],
        "recommendations": [
            "Monitor for changes in size, shape, or color",
            "Avoid excessive sun exposure",
            "Consult a dermatologist for suspicious changes"
        ],
        "expected_cure_time": "Usually does not require treatment unless malignant changes occur"
    },
    7: {
        "name": "Normal skin",
        "medicines": ["No medication required"],
        "recommendations": [
            "Maintain a balanced skincare routine",
            "Use sunscreen daily",
            "Stay hydrated and eat a balanced diet"
        ],
        "expected_cure_time": "Not applicable"
    },
    8: {
        "name": "Oily skin",
        "medicines": ["Oil-control cleansers", "Salicylic Acid-based products", "Niacinamide serums"],
        "recommendations": [
            "Use non-comedogenic products",
            "Avoid over-washing your face",
            "Blot excess oil during the day"
        ],
        "expected_cure_time": "Ongoing management required; no permanent cure"
    },
    9: {
        "name": "Pigmented benign keratosis",
        "medicines": ["Cryotherapy", "Curettage", "Electrosurgery (if removal is necessary)"],
        "recommendations": [
            "Monitor for changes in appearance",
            "Protect skin from UV radiation",
            "Consult a dermatologist if lesions become bothersome"
        ],
        "expected_cure_time": "Varies; usually treated quickly if necessary"
    },
    10: {
        "name": "Seborrheic keratosis",
        "medicines": ["Cryotherapy", "Curettage", "Laser Therapy (if required)"],
        "recommendations": [
            "Avoid picking or scratching at lesions",
            "Use gentle skincare products",
            "Consult a dermatologist for removal if bothersome"
        ],
        "expected_cure_time": "Does not require treatment unless removal is needed"
    },
    11: {
        "name": "Squamous cell carcinoma",
        "medicines": ["Surgical Removal", "Topical Chemotherapy", "Radiation Therapy"],
        "recommendations": [
            "Regular follow-ups with a dermatologist",
            "Protect skin from UV exposure",
            "Adhere strictly to treatment plans"
        ],
        "expected_cure_time": "Depends on the stage; early detection is key"
    },
    12: {
        "name": "Vascular lesion",
        "medicines": ["Laser Therapy", "Electrosurgery (if removal is necessary)", "Topical Treatments (if prescribed)"],
        "recommendations": [
            "Monitor for changes in size or appearance",
            "Avoid trauma to the area",
            "Consult a dermatologist for cosmetic concerns"
        ],
        "expected_cure_time": "Depends on the type and treatment; cosmetic improvements can be immediate"
    }
}
            
            condition = conditions_data.get(int(predicted_class_index), None)
            return render_template("skinresult.html",condition=condition)
    return render_template("skinhome.html")



BASE_DIR1 = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER1 = os.path.join(BASE_DIR1, "UPLOAD_FOLDER1")
app.config['UPLOAD_FOLDER1'] = UPLOAD_FOLDER1
if not os.path.exists(app.config['UPLOAD_FOLDER1']):
    os.makedirs(app.config['UPLOAD_FOLDER1'])
MODEL_PATH1 = os.path.join(BASE_DIR1, "blood_model.h5")
loaded_model1 = load_model(MODEL_PATH1)



@app.route('/blood_home', methods=['GET', 'POST'])
def upload_fildse1():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part in the request.')
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            flash('No selected file.')
            return redirect(request.url)
        
        if file:
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER1'], filename)
            file.save(filepath)
            
            # Preprocess image and make a prediction
            image_data = preprocess_image(filepath)
            prediction = loaded_model1.predict(image_data)
            predicted_class_index = prediction.argmax()  # Get the index of the highest probability
            details = {
        "3": {
            "label": "[Malignant] Early Pre-B",
            "description": "Early Pre-B leukemia is a subtype of acute lymphoblastic leukemia (ALL) characterized by immature B-cell precursors. It requires immediate medical attention and a tailored treatment plan.",
            "medications": "Treatment often includes chemotherapy agents like vincristine, cyclophosphamide, and methotrexate, along with corticosteroids."
        },
        "1": {
            "label": "[Malignant] Pre-B",
            "description": "Pre-B leukemia is a malignancy involving B-cell precursors at a slightly advanced stage compared to Early Pre-B. It is commonly seen in children and requires a detailed diagnostic and therapeutic approach.",
            "medications": "Standard treatment includes a combination of chemotherapy drugs, potential use of targeted therapies like monoclonal antibodies, and bone marrow transplant if required."
        },
        "2": {
            "label": "[Malignant] Pro-B",
            "description": "Pro-B leukemia is a highly aggressive form of ALL, involving the earliest B-cell precursors. Early diagnosis and aggressive treatment are crucial.",
            "medications": "Intensive chemotherapy protocols are the mainstay, sometimes followed by immunotherapy or stem cell transplantation."
        },
        "0": {
            "label": "Benign",
            "description": "The result suggests a benign condition, which typically does not require aggressive treatment. However, further evaluation may be recommended to rule out other issues.",
            "medications": "No specific treatment is required, but routine monitoring and supportive care may be advised."
        }

    }
        info= details[str(predicted_class_index)]
        return render_template('blood_res.html', label=info['label'], description=info['description'], medications=info['medications'])
    return render_template("blood_home.html")




@app.route("/lung")
def hodsme():
    return render_template("lung_home.html")  # Serve the HTML form



@app.route("/submitlung", methods=["POST"])
def submit():
    
    if request.method == "POST":
        # Collect data from the form
        age = int(request.form["age"])
        smoking = request.form["smoking"]
        yellow_fingers = request.form["yellow_fingers"]
        anxiety = request.form["anxiety"]
        peer_pressure = request.form["peer_pressure"]
        chronic_disease = request.form["chronic_disease"]
        fatigue = request.form["fatigue"]
        allergy = request.form["allergy"]
        wheezing = request.form["wheezing"]
        alcohol_consuming = request.form["alcohol_consuming"]
        coughing = request.form["coughing"]
        shortness_of_breath = request.form["shortness_of_breath"]
        swallowing_difficulty = request.form["swallowing_difficulty"]
        chest_pain = request.form["chest_pain"]

        # Create the feature array
        features = np.array([[ smoking == "Yes", yellow_fingers == "Yes", anxiety == "Yes",
                              peer_pressure == "Yes", chronic_disease == "Yes", fatigue == "Yes",
                              allergy == "Yes", wheezing == "Yes", alcohol_consuming == "Yes",
                              coughing == "Yes", shortness_of_breath == "Yes", swallowing_difficulty == "Yes",
                              chest_pain == "Yes"]])

        # Scale the features
        features_scaled = Scaler.transform(features)

        # Predict the result using the trained model
        prediction = model.predict(features_scaled)

        # Decode the prediction (0 or 1)
        result = "Positive" if prediction[0] == 1 else "Negative"
        return render_template("result_lung.html", result=result)




BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "UPLOAD_FOLDER")
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])
MODEL_PATH = os.path.join(BASE_DIR, "saved_cancer_model.h5")
loaded_model = load_model(MODEL_PATH)


@app.route('/kidney_home', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part in the request.')
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            flash('No selected file.')
            return redirect(request.url)
        
        if file:
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Preprocess image and make a prediction
            image_data = preprocess_image(filepath)
            prediction = loaded_model.predict(image_data)
            predicted_class_index = prediction.argmax()  # Get the index of the highest probability
            dict={'0':'Grade 0','1':'Grade 1','2':'Grade 2','3':'Grade 3','4':'Grade 4'}
            res = dict[str(predicted_class_index)]
            return render_template("kidney_res.html", result=res)

    return render_template("kidney_home.html")

@app.route("/con")
def fun7():
    if(os.path.exists(fr"C:\Users\saikarthik\Desktop\New Doctor\patient_data\{session["patient"]}.txt")):
        f=open(fr"C:\Users\saikarthik\Desktop\New Doctor\patient_data\{session["patient"]}.txt")
        r=eval(f.read())
        return render_template("myself.html",patdict=r)
    fi = fr"C:\Users\saikarthik\Desktop\NEW PATIENT\patient_data\{session["patient"]}.txt"
    f=open(fi)
    r=f.read()
    patdict = eval(r)
    return render_template("patdetails.html",email=session["patient"],name=patdict["name"],age=patdict["age"],gender=patdict["gender"],weight=patdict["weight"],height=patdict["height"],blood_type=patdict["blood_type"],symptoms=patdict["symptoms"],fam=patdict["family_history"])



@app.route("/docpres", methods=["GET", "POST"])
def fundoc():
    if request.method == "POST":
        form_data = {key: value for key, value in request.form.items()}
        curt = form_data.get('PatientID') 
        fi = fr"C:\Users\saikarthik\Desktop\NEW DOCTOR\patient_data\{curt}.txt"
        f=open(fi,"w")
        f.write(str(form_data))
        f.close()
        f=open(fr"C:\Users\saikarthik\Desktop\New Patient\status\{curt}.txt","w")
        f.write("1")
        f.close()
        sender_email = "cancer.therapy.free.org@gmail.com"
        receiver_email = curt
        password = "tncz bhfi qoqa lube"  
        subject = "Reports From Doctor"
        body = """
Hello,

We have received your reports. You can view them under the "Prescription" section on our website.

Best regards,
Oncology Care Team"""
        msg = EmailMessage()
        msg['Subject'] = subject
        msg['From'] = sender_email
        msg['To'] = receiver_email
        msg.set_content(body)
        try:
            with smtplib.SMTP('smtp.gmail.com', 587) as server:
                server.starttls()  # Secure the connection
                server.login(sender_email, password)  # Login to the email account
                server.send_message(msg)  # Send the email
                print("Email sent successfully!")
        except Exception as e:
            print(f"An error occurred: {e}")
        return render_template("mar.html", message="Sent the Prescription to patient.... redirecting")
        

app.run(port=8000)