from enum import unique
from datetime import datetime
from flask import Flask,request
import base64
import cv2
import io
import time
from imageio import imread
import numpy as np
import sqlite3

import efficientnet.keras as efn
from tensorflow.keras.models import load_model
from functions import *

import matplotlib.pyplot as plt
import uuid
import os


IMG_SIZE = (128,128)
SAVE_FOLDER = "images/"

app = Flask(__name__)
model = load_model('disease.model')

def register_account(email,passw,age,gender,fname,lname,database = "MedicalAI.db"):
    """
    Return codes:
        0 - Works
        1 - Account exists
        -1 - Something went wrong
    """

    con = sqlite3.connect(database)
    cursor = con.cursor()
    query = "SELECT * FROM accounts WHERE email = (?)"
    result = cursor.execute(query,(email,))
    if len(list(result)) >= 1:
        con.close()        
        return "1%Account already exists"
    
    query = "INSERT INTO accounts ('email','password','age','gender','fname','lname') VALUES (?,?,?,?,?,?)"
    result = cursor.execute(query,(email,passw,age,gender,fname,lname,))

    con.commit()
    con.close()
    return "0%{}%{}%{}%{}%{}".format(email,age,gender,fname,lname)
    

def login_account(email,passw,database = "MedicalAI.db"):
    """
    Return codes:
        0 - Works
        1 - Account doesn't exist
        -1 - Something went wrong.
    """

    

    con = sqlite3.connect(database)
    cursor = con.cursor()
    query = "SELECT * FROM accounts WHERE email = (?) and password = (?)"
    result = cursor.execute(query,(email,passw,))
    k = 0
    r = []
    for row in result:
        k+=1
        r = row
    if k == 0:        
        con.close()
        return "1%Account not found"

    elif k == 1:
        con.close()
        return "0%{}%{}%{}%{}%{}".format(r[1],r[3],r[4],r[5],r[6])

    con.close()

    return "1%Something went wrong"
def get_records(email,database = "MedicalAI.db"):
    """
    Return codes:
        0 - Works
        1 - Account doesn't exist
        -1 - Something went wrong.
    """

    

    con = sqlite3.connect(database)
    cursor = con.cursor()
    query = "SELECT * FROM records WHERE email = (?)"
    result = cursor.execute(query,(email,))
    k = 0
    r = []
    for row in result:
        k+=1
        r.append(row)

    con.close()
    return r

def insert_record(email,image_id,date,output,accuracy,database = "MedicalAI.db"):
    """
    Return codes:
        0 - Works
        1 - Account exists
        -1 - Something went wrong
    """

    con = sqlite3.connect(database)
    cursor = con.cursor()

    query = "INSERT INTO records ('email','image','date','result','accuracy') VALUES (?,?,?,?,?)"
    result = cursor.execute(query,(email,image_id,date,output,accuracy,))

    con.commit()
    con.close()
    return 0
    

def predict():
    
    img = cv2.imread('./1.jpg')
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = cv2.resize(img,IMG_SIZE)
    X = np.expand_dims(img,axis=0)

    pred = model.predict(X)

@app.route('/test',methods=['POST'])
def test():
    tst = request.form['test']
    
    print(tst)


@app.route('/getRecords',methods=['POST'])
def getRecords():
    email = request.form['email']
    res = get_records(email)

    # We need to make the results so that we can process them on the phone.
    # The delimitors between records is %, and between the values is &
    result_string = ""
    for row in res:

        result_string += row[ 2] # image
        result_string += "%"
        result_string += row[3] # date
        result_string += "%"
        result_string += row[4] # result
        result_string += "%"
        result_string += row[5] # accuracy

        result_string += "&"
        
    result_string = result_string[:-1]


    return result_string
    
@app.route('/login',methods=['POST'])
def login():
    email = request.form['email']
    password = request.form['password']
    email = email.lower()
    print(email)
    print(password)
    res = login_account(email,password)
    return res
    

@app.route('/register',methods=['POST'])
def register():
    email = request.form['email']
    password = request.form['password']
    age = request.form['age']
    gender = request.form['gender']
    fname = request.form['fname']
    lname = request.form['lname']
    email = email.lower()
    print(email)
    print(password)
    print(age)
    print(gender)
    res = register_account(email,password,age,gender,fname,lname)
    return res

def encode_site(x):
    sites = {
        "torso":0,
        "lower extremity":1,
        "upper extremity":2,
        "head/neck":3,
        "palms/soles":4,
        "oral/genital":5,
        "unknown":6
    }
    return sites[x]

encoded_results = {
    0:'Keratosis-like lesion',
    1:'Melanocytic nevi',
    2:'Dermatofibroma',
    3:'Melanoma',
    4:'Vascular lesion',
    5:'Basal cell carcinoma',
    6:'Actinic keratosis'
}

@app.route('/sendImage',methods=['POST'])
def get():
    
    if request.method == 'POST':
        start = time.time()

        fileImg = request.form['image']
        email = request.form['email']        
        print("fileImg")
        print(fileImg[:50])

        unique_filename = str(uuid.uuid4())+".jpeg"

        img = imread(io.BytesIO(base64.b64decode(fileImg)))           

        # Convert it to cv2 and resize to 512x512
        img = cv2.resize(img,(512,512))
        img = cv2.cvtColor(img,cv2.COLOR_RGB2BGR)
        
        img_to_send = img.copy()
        img_to_send = getImageWithContour(img_to_send)

        img_str = cv2.imencode('.jpeg', img_to_send)[1].tostring()
        img_str = base64.b64encode(img_str)

        img = cv2.resize(img,(128,128))

        X = np.expand_dims(img,axis=0)
        np.set_printoptions(suppress=True)
        pred = model.predict(X)
        # Getting which one is correct
        mi = np.argmax(pred[0])
        print("DEB")
        print("Array:",pred)
        print("Result:",mi)
        print("Full name:",encoded_results[mi])
        print("Accurcay:",pred[0][mi])

        print("Request done in:",time.time()-start)


        today = datetime.today().strftime('%d.%m.%Y')
        cv2.imwrite(os.path.join(SAVE_FOLDER,unique_filename),img)
        
        insert_record(email,img_str.decode("utf-8"),today,encoded_results[mi],str(pred[0][mi]))

        return encoded_results[mi]+"%"+str(pred[0][mi])+"%"+img_str.decode("utf-8")

    return "ERROR"
    

if __name__ == "__main__":
    try:        
        app.run(host='0.0.0.0',threaded=False,port=5000)      

    except Exception as e:
        print(e)