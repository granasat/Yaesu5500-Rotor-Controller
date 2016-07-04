#!/usr/bin/python2
# -*- coding: utf-8 -*-

import serial
import os
import logging
import config
from datetime import timedelta
from flask import Flask, render_template, request, url_for, redirect, session, flash

app = Flask(__name__)

app.secret_key = os.urandom(24)

app.permanent_session_lifetime = timedelta(seconds=120)

ser = serial.Serial(
    port=config.serial_port,
    baudrate=config.serial_baudrate,
	timeout=0,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.EIGHTBITS
)

logger = logging.getLogger('rotor_control')
hdlr = logging.FileHandler(config.log_file)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr) 
logger.setLevel(logging.DEBUG)

last_az = -1
last_el = -1
user_logged = 0

@app.route("/")
def index():
	if not session.get('logged_in'):
	    return render_template('index.html')
	else:
	    return render_template('control.html')
	
@app.route("/login")
def login():
    if not session.get('logged_in'):
        return render_template('login.html')
    else:
        return render_template('control.html')

@app.route("/logout")
def logout():
    global user_logged
    session['logged_in'] = False
    user_logged = 0
    logger.info('User admin logout.')
    return index()
	
@app.route('/doLogin', methods=['POST'])
def do_admin_login():
    global user_logged
    session.permanent = True
    if user_logged == 0:
        if request.form['username'] == config.username and request.form['password'] == config.password:
            session['logged_in'] = True
            user_logged = 1
            logger.info('User admin logged from '+request.remote_addr)
        else:
            flash('Wrong identification!')
            logger.error('Wrong logging attempt from '+request.remote_addr)
    else:
        flash('Web Control is currently in use.')
    return login()
	
@app.route("/getData/<data>",methods=['GET'])
def getData(data):
    global last_az
    global last_el
    if (last_az == -1 or last_el == -1):
        print ("Reading from COM Port")
        if ser.isOpen():
            ser.write('C2 \n')
            while ser.inWaiting() == 0:
                pass
            serialData = ser.readline()
            tam=len(serialData.split('+0'))
            print (serialData)
            last_az = serialData.split('+0')[1]
            last_el = (serialData.split('+0')[2]).strip()
            if data == "azimut":
                return last_az
            elif data == "elevation":
                return last_el
        else:
            return "Error Reading COM Port"
    else:
        print ("Reading from Cache")
        if data == "azimut":
            return last_az
        elif data == "elevation":
            return last_el
		
@app.route("/getDataLgd/<data>",methods=['GET'])
def getDataLgd(data):
    global last_az
    global last_el

    if ser.isOpen():
        ser.write('C2 \n')
        while ser.inWaiting() == 0:
            pass
        serialData = ser.readline()
        tam=len(serialData.split('+0'))
        print (serialData)
        last_az = serialData.split('+0')[1]
        last_el = (serialData.split('+0')[2]).strip()
        if data == "azimut":
            return last_az
        elif data == "elevation":
            return last_el
    else:
        return "Error Reading COM Port"
		
@app.route("/sendData")
def sendData():
    if session.get('logged_in'):
        _az = request.args.get('a')
        _el = request.args.get('e')
        if ser.isOpen():
            ser.write('W'+_az+' '+_el)
            #ser.write('W'+_az)
            print("Go to: az: "+_az+", el: "+_el)
            logger.info('User moved to Az: '+_az+', El: '+_el)
            return "OK"
        else:
            return "Error Reading COM Port"
    else:
        flash('Session expired.')
        return login()
		
@app.route("/sendStop")
def sendStop():
    if session.get('logged_in'):
        if ser.isOpen():
            ser.write('S')
            print("STOP Signal sent")
            logger.info('User sent STOP signal.')
            return "Ok"
        else:
            return "Error"
    else:
        flash('Session expired.')
        return login()
		
if __name__ == "__main__":
    app.run(host='0.0.0.0',port=3000,debug=True)
