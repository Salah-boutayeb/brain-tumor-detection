from flask import Flask
import os
import requests

from flask import Flask, render_template, flash, redirect, url_for, session, logging, request, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from PIL import Image
import torch
from ultralytics.yolo.engine.model import YOLO
""" **************************************** """

UPLOAD_FOLDER = 'src/WebApp/static'
ALLOWED_EXTENSIONS = ['png', 'jpg', 'jpeg']

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = "m4xpl0it"


uploads_dir = os.path.join(app.instance_path, 'uploads')
save_dir = os.path.join(app.instance_path, 'save')

# Load your trained model
model = YOLO("C:\\Users\\bouta\\OneDrive\\Bureau\\random project\\brain_tumor_detection\\BrainTumorVision\\src\\WebApp\\detect\\brain_tumor_custom_#42\\weights\\best.pt")


class user(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80))
    email = db.Column(db.String(120))
    password = db.Column(db.String(80))


class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(80))
    prenom = db.Column(db.String(120))
    telephone = db.Column(db.String(80))
    email = db.Column(db.String(80))
    etat = db.Column(db.String(80))
    barin_image_url = db.Column(db.String(200))


def segm(file_path, filename, nom, prenom, phone, email):
    print(file_path, filename)
    imgs = Image.open(file_path)
    with torch.no_grad():
        res = model.predict(imgs)
        boxes = res[0].boxes
        res_plotted = res[0].plot()[:, :, ::-1]
        output_path = os.path.join(
            app.config['UPLOAD_FOLDER']+'/save/', 'plotted_image_'+filename)

        Image.fromarray(res_plotted).save(output_path)
        for r in res:
            for c in r.boxes.cls:
                print(model.names[int(c)])

                if model.names[int(c)] == 'brain_tumor':
                    # st.error("Brain Tumor detection, seek immediate health care", icon="🚨")
                    patient = Patient(nom=nom, prenom=prenom, email=email, telephone=phone, etat="Brain Tumor detection, seek immediate health care.",
                                      barin_image_url=url_for('static/save/'+'plotted_image_'+filename))
                    db.session.add(patient)
                    db.session.commit()
                    return render_template('pred.html', pred="Brain Tumor detection, seek immediate health care 🚨", f_name='save/plotted_image_'+filename, patient=patient)
    patient = Patient(nom=nom, prenom=prenom, email=email, telephone=phone, etat="No Brain Tumor detected.", barin_image_url=url_for('static', filename='/upload'+filename))
    db.session.add(patient)
    db.session.commit()
    return render_template('pred.html', pred="No Brain Tumor detected", f_name='save/plotted_image_'+filename, patient=patient)




@ app.route("/")
def index():
    return render_template("index.html")


@ app.route("/user")
def index_auth():
    return render_template("index_auth.html")


@ app.route("/instruct")
def instruct():
    return render_template("instructions.html")


@ app.route('/pred_page')
def pred_page():
    pred=session.get('pred_label', None)
    f_name=session.get('filename', None)
    return render_template('pred.html', pred=pred, f_name=f_name)


@ app.route("/upload", methods=['POST', 'GET'])
def upload():
    try:
        if request.method == 'POST':
            f=request.files['bt_image']
            patient_nom=request.form['nom']
            patient_prenom=request.form['prenom']
            patient_email=request.form['email']
            patient_telephone=request.form['telephone']


            filename=secure_filename(f.filename)
            f.save(os.path.join(
                app.config['UPLOAD_FOLDER']+'/upload/', filename))
            return segm(os.path.join(app.config['UPLOAD_FOLDER']+'/upload/', filename), filename, patient_nom, patient_prenom, patient_telephone, patient_email)

    except Exception as e:
        print("Exception\\n")
        print(e, '\\n')

    return render_template("upload.html")


@ app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        uname=request.form["uname"]
        passw=request.form["passw"]

        login=user.query.filter_by(username=uname, password=passw).first()
        if login is not None:
            return redirect(url_for("index_auth"))
    return render_template("login.html")


@ app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        uname=request.form['uname']
        mail=request.form['mail']
        passw=request.form['passw']

        register=user(username=uname, email=mail, password=passw)
        db.session.add(register)
        db.session.commit()

        return redirect(url_for("login"))
    return render_template("register.html")


if __name__ == "__main__":
    # Ajouter le contexte d'application avant la création des tables
    with app.app_context():
        db.create_all()

    app.run(debug=True, port=3000)
