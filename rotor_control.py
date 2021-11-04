#!/usr/bin/python2
# -*- coding: utf-8 -*-

import serial
import os
import logging
import time
import config
from datetime import timedelta
from flask import Flask, render_template, request, url_for, redirect, session, flash

app = Flask(__name__)

app.secret_key = os.urandom(24)

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
last_seen_user_logged = 0


def isactive_lastseen(local_session, cur_time):
    if not local_session.get('last_seen'):
        return False

    active = cur_time - local_session['last_seen'] < config.max_unusedtime \
        and local_session['last_seen'] < cur_time
    if not active and local_session.get('logged_in'):
        local_session['logged_in'] = False
    return active

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
    global last_seen_user_logged
    cur_time = time.time()
    lastseen_elapsed = cur_time - last_seen_user_logged
    if user_logged == 0 or lastseen_elapsed > config.max_unusedtime:
        if request.form['username'] == config.username and request.form['password'] == config.password:
            last_seen_user_logged = cur_time
            session['last_seen'] = cur_time
            session['logged_in'] = True
            user_logged = 1
            logger.info('User admin logged from '+request.remote_addr)
        else:
            flash('Wrong identification!')
            logger.error('Wrong logging attempt from '+request.remote_addr)
    else:
        flash(('Web Control is currently in use. '
               f'Last seen logged user {cur_time - last_seen_user_logged:.2f} '
               'seconds ago.'))
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
    cur_time = time.time()
    if session.get('logged_in') and isactive_lastseen(session, cur_time):
        _az = request.args.get('a')
        _el = request.args.get('e')
        if ser.isOpen():
            ser.write(('W'+_az+' '+_el).encode())
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
    cur_time = time.time()
    if session.get('logged_in') and isactive_lastseen(session, cur_time):
        if ser.isOpen():
            ser.write(('S').encode())
            print("STOP Signal sent")
            logger.info('User sent STOP signal.')
            return "Ok"
        else:
            return "Error"
    else:
        flash('Session expired.')
        return login()

@app.route("/keepAlive", methods=['GET'])
def keepAlive():
    global last_seen_user_logged
    if session.get('logged_in') and isactive_lastseen(session, time.time()):
        last_seen_user_logged = time.time()
        session['last_seen'] = last_seen_user_logged
        return f"Last seen at {last_seen_user_logged}", 200

    return "Must be logged in", 400


if __name__ == "__main__":
    app.run(host='0.0.0.0',port=3000,debug=True)
