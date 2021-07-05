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


import matplotlib.pyplot as plt

IMG_SIZE = (128,128)


app = Flask(__name__)
model = load_model('disease.model')

def register_account(email,passw,database = "MedicalAI.db"):
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
        return 1

    query = "INSERT INTO accounts ('email','password') VALUES (?,?)"
    result = cursor.execute(query,(email,passw,))

    con.commit()

    con.close()

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

    con.close()

    if len(list(result)) == 0:        
        return 1

    elif len(list(result)) == 1:
        return 0

    return -1


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
@app.route('/login',methods=['POST'])
def login():
    email = request.form['email']
    password = request.form['password']
    email = email.lower()
    print(email)
    print(password)
    # login_account(email,password)

@app.route('/register',methods=['POST'])
def register():
    email = request.form['email']
    password = request.form['password']
    email = email.lower()
    print(email)
    print(password)
    register_account(email,password)

@app.route('/sendImage',methods=['POST'])
def get():
    
    if request.method == 'POST':
        start = time.time()

        fileImg = request.form['image']
        fileID = request.form['id']

        print("Processing request from id= "+str(fileID))
        img = imread(io.BytesIO(base64.b64decode(fileImg)))                   

        img = cv2.resize(img,(128,128))

        X = np.expand_dims(img,axis=0)

        pred = model.predict(X)
        print("Request done in:",time.time()-start)
        print(pred[0][0])
        return str(pred[0][0])        

    return "ERROR"
    

if __name__ == "__main__":
    try:        
        # app.debug=True
        # 86.125.92.85
        # predict()
        app.run(host='0.0.0.0',threaded=False,port=5050)      

    except Exception as e:
        print(e)
    



