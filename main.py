from flask import Flask, request, render_template, redirect, url_for , session
import pymysql
import pandas
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
import matplotlib.pyplot as plt
import io
import base64
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
import ast
from docx.shared import Pt, RGBColor
import smtplib
from email.message import EmailMessage
import json
import pandas as pd
from pymysql.cursors import DictCursor
from datetime import timedelta

app = Flask(__name__)
app.secret_key = "gitamuniversity"  
app.permanent_session_lifetime = timedelta(minutes=30)
clr = load("random_forest_model.joblib")
scaler = load("scaler.joblib")
labelencoder = load("label_encoder.joblib")
model = joblib.load('cancersmodel.pkl')

patdict={}

connection = pymysql.connect(
    host='127.0.0.1',
    user='root',
    password='',
)
cursor = connection.cursor()
cursor.execute('''use patient;''')

@app.before_request
def make_session_permanent():
    session.permanent = True

userrr = ''
@app.route("/")
def fun1():
    return render_template("loginPage.html")
    session["user"]=""


@app.route("/new", methods=['POST'])
def fun2():
    user = request.form.get("name")  
    email = request.form.get("email")
    pas = request.form.get("password")
    cursor.execute(f'''SELECT email FROM details WHERE email="{email}";''')
    dat = cursor.fetchone()
    if(dat):
        return "Account already exists"
    else:
        cursor.execute(f'''INSERT INTO details VALUES("{user}", "{email}", "{pas}");''')
        connection.commit()
        return "account_created"  
    return render_template("loginPage.html")





@app.route("/login", methods=['POST', 'GET'])
def fun3():
    user = request.form.get("email")  
    pas = request.form.get("password")
    cursor.execute(f'''select email,password from details where email="{user}";''')
    dat = cursor.fetchone()
    if(dat is None):
        return "not_found"
    else:
        user1,pas1 = dat
        if(user1 == user and pas == pas1):
            global userrr
            userrr=user1
            session["user"] = user
            return render_template("homePage.html")
        else:
            return "invalid"
    return render_template("loginPage.html")

@app.route("/home")
def fun4():
    if(os.path.exists(fr"C:\Users\saikarthik\Desktop\New Patient\status\{session["user"]}.txt")):
        return render_template("homepage1.html")
    return render_template("homePage.html")

@app.route("/about")
def fun5():
    return render_template("about_us.html")    

@app.route("/presdoc")
def fun11():
    f=open(fr"C:\Users\saikarthik\Desktop\New Doctor\patient_data\{session["user"]}.txt")
    r=eval(f.read())
    return render_template("doctorres.html",patdict=r)

@app.route("/jag")
def jag():
    return redirect(f"http://127.0.0.1:5001/?user_id={session["user"]}")


@app.route("/bloodtest")
def fun12():
    if(os.path.exists(fr"C:\Users\saikarthik\Desktop\New Patient\patient_lab\{session["user"]}.txt")):
        f=open(fr"C:\Users\saikarthik\Desktop\New Patient\patient_lab\{session["user"]}.txt","r")
        r=eval(f.read())
        return render_template("mybooked.html",info=r)
    f=open(fr"C:\Users\saikarthik\Desktop\New Doctor\patient_data\{session["user"]}.txt")
    r=eval(f.read())
    return render_template("testres.html",patdict=r)

@app.route("/basictest")
def fun6():
    filename = f"patient_data/{session["user"]}.txt"
    if(os.path.exists(filename)):
        f=open(filename)
        patdict=eval(f.read())
        return render_template("initreport.html",data=patdict)
    else:
        print("2.0")
        m=session["user"]
        cursor.execute(f'''select * from appointments where patient="{m}";''')
        dat = cursor.fetchone()
        if(dat):
            f=open(fr"patient_data/{session["user"]}.txt")
            patdict=eval(f.read())
            return render_template("initreport.html",data=patdict)
    return render_template("basictest.html")

@app.route("/con")
def fun10():
    return redirect(f"http://127.0.0.1:5001/?user_id={session["user"]}")

    
@app.route("/bookme")
def fun13():
    return render_template("lab.html")

@app.route("/fromlab",methods=["POST","GET"])
def fun14():
    if(request.method=='POST'):
        pat={}
        pat["patient_phone"] = request.form.get("patientPhone")
        pat["test_type"] = request.form.get("testType")
        pat["selected_date"] = request.form.get("selectedDate")  
        pat["selected_time"] = request.form.get("selectedTime") 
        f=open(fr"patient_lab/{session["user"]}.txt","w")
        json.dump(pat, f, indent=4)   
        f.close()
        return render_template("mar1.html",message="Successfully booked your lab test ")


@app.route('/step2', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        symptoms = { 
            'unusual_mole': 1 if request.form.get('unusual_mole') == 'on' else 0,
            'skin_sore': 1 if request.form.get('skin_sore') == 'on' else 0,
            'itchy_mole': 1 if request.form.get('itchy_mole') == 'on' else 0,
            'persistent_cough': 1 if request.form.get('persistent_cough') == 'on' else 0,
            'cough_blood': 1 if request.form.get('cough_blood') == 'on' else 0,
            'shortness_breath': 1 if request.form.get('shortness_breath') == 'on' else 0,
            'bruising': 1 if request.form.get('bruising') == 'on' else 0,
            'recurrent_fever': 1 if request.form.get('recurrent_fever') == 'on' else 0,
            'fatigue': 1 if request.form.get('fatigue') == 'on' else 0,
            'blood_urine': 1 if request.form.get('blood_urine') == 'on' else 0,
            'back_pain': 1 if request.form.get('back_pain') == 'on' else 0,
            'weight_loss': 1 if request.form.get('weight_loss') == 'on' else 0,
        }
        input_data = pd.DataFrame([symptoms])
        prediction = model.predict(input_data)[0]
        return render_template('cancertype.html', prediction=prediction)
    return render_template('typepred.html', prediction=None)


@app.route("/step3")
def fun7():
    type = request.args.get("type")
    patdict["cancertype"] = type 
    cursor.execute(f'''select name from alldoc where type="{type}";''')
    dat = cursor.fetchall()
    return render_template("showdoctor.html",doctors=dat)


@app.route("/book", methods=["GET", "POST"])
def fun8():
    if request.method == "POST":
        # Get form data
        doctor_name = request.form.get("doctor_name")
        patient_name = request.form.get("patient_name")
        patdict["name"] = patient_name
        date = request.form.get("date")
        time = request.form.get("time")
        cursor.execute('''SELECT COUNT(*) as count FROM appointments 
                          WHERE doctor_name = %s AND date = %s''', (doctor_name, date))
        result = cursor.fetchone()
        if(result is None):
            appointment_count = 0
        else:
            appointment_count = result[0]
        if appointment_count >= 10:
            return render_template("booking.html", doctor_name=doctor_name, message="Doctor is fully booked for the selected date.")
        cursor.execute('''INSERT INTO appointments (doctor_name, date, time,patient) 
                          VALUES (%s, %s, %s,%s)''', (doctor_name, date, time,session["user"]))
        connection.commit()
        return redirect(url_for("fun9"))
    doctor_name = request.args.get("doctor")
    return render_template("booking.html", doctor_name=doctor_name)


@app.route("/prese",methods=["POST","GET"])
def fun9():
    if request.method == "POST":
        patdict['weight'] = request.form.get("weight")
        patdict['height'] = request.form.get("height")
        patdict['age'] = request.form.get("age")
        patdict['blood_type'] = request.form.get("bloodType")
        patdict['symptoms'] = request.form.get("symptoms")
        patdict['family_history'] = request.form.get("familyHistory")  
        filename = f"patient_data/{session["user"]}.txt"
        with open(filename, "w") as file:
            json.dump(patdict, file, indent=4)     
        return render_template("mar1.html",message="Successfully Sent to Doctor. will be receiving update soon.")
    return render_template("patientdetails.html")



@app.route("/submit", methods=["POST", "GET"])
def funj1():
    data = request.form
    feature_names = [
        'Alcoholuse', 'GeneticRisk', 'chronicLungDisease',
        'Smoking', 'ChestPain', 'CoughingofBlood', 'Fatigue',
        'WeightLoss', 'ShortnessofBreath', 'SwallowingDifficulty',
        'FrequentCold', 'DryCough'
    ]


    l = [
        int(data["alcohol"]),
        int(data["genetic_risk"]),
        int(data["chronic_lung_disease"]),
        int(data["smoking"]),
        int(data["chest_pain"]),
        int(data["coughing_blood"]),
        int(data["fatigue"]),
        int(data["weight_loss"]),
        int(data["shortness_of_breath"]),
        int(data["swallowing_difficulty"]),
        int(data["frequent_cold"]),
        int(data["dry_cough"]),
    ]
     
    patdict["alcohol"] = data["alcohol"]
    patdict["lungDisease"] = data["chronic_lung_disease"]
    patdict["smoke"] = data["smoking"]
    patdict["chestPain"] = data["chest_pain"]
    patdict["coughingBlood"] = data["coughing_blood"]
    patdict["fatigue"] = data["fatigue"]
    patdict["swallowingDifficulty"] = data["swallowing_difficulty"]
    patdict["cold"] = data["frequent_cold"]
    patdict["dryCough"] = data["dry_cough"]
    patdict["obesity"] = data["weight_loss"]
    patdict["gender"]  = data["gender"]
    x_test = pandas.DataFrame([l], columns=feature_names)
    x_test = scaler.transform(x_test)
    
    y_pred = clr.predict(x_test)
    prediction = labelencoder.inverse_transform(y_pred)[0]

    feature_importances = clr.feature_importances_ * 100  
    
    priority_weights = {
        'Alcoholuse': 2.0,      
        'Smoking': 1.5,        
        'GeneticRisk': 1.2,    
        'CoughingofBlood': 1.1  
    }
    
    for i, feature in enumerate(feature_names):
        if feature in priority_weights:
            feature_importances[i] *= priority_weights[feature]
    feature_importances = (feature_importances / np.sum(feature_importances)) * 100
    max_importance = np.max(feature_importances)
    top_indices = [i for i, imp in enumerate(feature_importances) if imp == max_importance]
    import random
    top_feature_idx = random.choice(top_indices)

    feature_data = list(zip(feature_names, l, feature_importances))
    if(prediction=='Low'):
        print("tes")
        return render_template(
        "result_data.html",
        prediction=prediction,
        feature_names=feature_names,
        feature_importances=list(feature_importances),
        feature_data=feature_data,
        top_feature=feature_names[top_feature_idx]
    )
    else:
        return render_template(
        "result_data1.html",
        prediction=prediction,
        feature_names=feature_names,
        feature_importances=list(feature_importances),
        feature_data=feature_data,
        top_feature=feature_names[top_feature_idx]
    )




app.run()