from flask import Flask,render_template, request, flash, url_for, redirect, session
from flask_pymongo import PyMongo
import pymongo
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime
import base64

app = Flask(__name__)
app.secret_key = "21pa1a1286@2025"

myclient = MongoClient("mongodb+srv://21pa1a1286:charishma@cluster0.nsdecj7.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")

#Patient db
patientdb = myclient["MediFace"]
patientcol = patientdb["patient-details"]
medicinecol = patientdb["medicine_details"]
testreports_col = patientdb["test_reports"]

# Worker db
logindb = myclient["Authentication"]
receptionistcol = logindb["User-details"]
data_entry_op_col = logindb["Data-entry-op-details"]


# d = list(patientcol.find().sort("date", pymongo.ASCENDING))
# print(d)

# Lander
@app.route("/",methods=['GET','POST'])
def lander():
    if request.method=='POST':
        user_name = request.form.get('username')
        password = request.form.get('pswd')
        login_type = request.form.get("flexRadioDefault")
        # x = logincol.insert_one({'username':user_name,'password':password})
        if login_type == "receptionist":
            if receptionistcol.find_one({"username":user_name,"password":password}):
                session['user'] = user_name
                flash('Login Successful','success')
                return redirect(url_for('wmain', username=user_name))
            else:
                flash('Invalid username or password','danger')
        elif login_type == "data_entry_operator":
            if data_entry_op_col.find_one({"username":user_name,"password":password}):
                session['user'] = user_name
                flash('Login Successful','success')
                return redirect(url_for('dmain', username=user_name))
            else:
                flash('Invalid username or password','danger')
    return render_template("lander.html")


# Worker Page
@app.route("/wmain/<username>",methods=['GET','POST'])
def wmain(username):
    if "user" in session:
        return render_template("home_worker.html",name=username)
    else:
        flash("Please login",'danger')
        return redirect(url_for('lander'))
    

 # Patient Page   
@app.route("/pmain",methods=['GET','POST'])
def pmain():
    if "user" in session:
        user = session['user']
        return render_template("home_patient.html",name=user)
    else:
        flash("Please login",'danger')
        return redirect(url_for('lander'))

    
# Data entry operator page
@app.route("/dmain/<username>", methods=['GET','POST'])
def dmain(username):
    if "user" in session:
        return render_template("home_dataeop.html", name=username)
    else:
        flash("Please login", 'danger')
        return redirect(url_for('lander'))

# New Form
@app.route("/form",methods=['GET','POST'])
def form():
    if request.method=='POST':
        name = request.form.get("name")
        age = request.form.get("age")
        gender = request.form.get("gender")
        place = request.form.get("place")
        mobile_no = request.form.get("number")
        symptoms = request.form.get("symptoms")
        doctor = request.form.get('doctor')
        status = request.form.get('status')
        current_date = datetime.now()
        x = patientcol.insert_one({"name": name, "age": age, "gender": gender, "status":status, "place": place, "mobile_number": mobile_no, "appointment":{"0":[current_date,symptoms,doctor]}})
        flash("Appointment Booked","success")
        return redirect(url_for("wmain",username=session.get('user')))
    return render_template("form_new.html")


# Existing Form
@app.route("/eform",methods=["GET","POST"])
def eform():
    if request.method=='POST':
        health_condition = request.form.get("symptoms")
        doctor = request.form.get("doctor")
    
        patient_details_cursor = patientcol.find({"name": "Naresh"})
        for patient_detail in patient_details_cursor:
            appointments = patient_detail.get("appointment", [])
            print(appointments)
            appointments[str(len(appointments))]=[datetime.now(), health_condition, doctor]
            patientcol.update_one({"_id": patient_detail["_id"]}, {"$set": {"appointment": appointments}})
        flash("Appointment Booked","success")
        return redirect(url_for("wmain",username=session.get('user')))
    return render_template("form_existing.html")

# Medicine Form
@app.route("/mform",methods=["GET","POST"])
def mform():
    if request.method=='POST':
        medicine = request.form.get("medicine")
        med = medicinecol.insert_one({'prescription':medicine})
        flash("Prescription Uploaded","success")
        return redirect(url_for("dmain",username=session.get('user')))
    return render_template("form_medicine.html")


@app.route('/tform')
def index():
    return render_template('form_testreports.html')

def b64encode_filter(content):
    return base64.b64encode(content).decode('utf-8')
app.jinja_env.filters['b64encode'] = b64encode_filter

@app.route('/upload', methods=['POST'])
def upload_file():
    patient_id = request.form['patient_id']
    if 'file' not in request.files:
        return 'No file part in the request'
    file = request.files['file']
    if file.filename == '':
        return 'No selected file'
    if file:
        # Read the file content
        file_content = file.read()
        # Encode the file content as Base64
        encoded_content = base64.b64encode(file_content)
        # Insert the encoded content into MongoDB
        testreports_col.insert_one({'patient_id': patient_id ,'filename': file.filename, 'content': encoded_content})
        return 'File uploaded successfully'
    

@app.route('/reports')
def list_files():
    files = testreports_col.find()  # Query MongoDB for files associated with the patient ID
    decoded_files = []
    for file in files:
        decoded_content = base64.b64decode(file['content'])
        decoded_files.append({'patient_id': file['patient_id'], 'filename': file['filename'], 'content': decoded_content})
    # Pass the decoded files to the HTML template
    return render_template('testreports.html', files=decoded_files)


# Logout
@app.route("/logout")
def logout():
    session.pop("user",None)
    flash("You have been logged out",'danger')
    return redirect(url_for('lander'))


# Profile
@app.route("/profile")
def profile():
    return render_template("profile.html")

# Prescription
@app.route("/prescription")
def prescription():
    return render_template("prescription.html")

# Medical History
@app.route("/history")
def medical_history():
    return render_template("medical_history.html")


# def retrieve(id):
#     x = patientcol.find({'_id':OjectId(id)})
#     return x

if __name__ == "__main__":
    app.run(debug=True)