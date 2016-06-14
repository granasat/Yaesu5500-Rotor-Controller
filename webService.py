import serial
from flask import Flask, render_template, request, url_for, redirect

app = Flask(__name__)

ser = serial.Serial(
    port='/dev/ttyUSB0',
    baudrate=9600,
	timeout=1,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.EIGHTBITS
)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/getData/<data>",methods=['GET'])
def getData(data):
    if ser.isOpen():
        ser.write('C2 \n')
        while ser.inWaiting() == 0:
			pass
			serialData = ser.readline()
			tam=len(serialData.split('+0'))
			print serialData
			if data == "azimut":
				return serialData.split('+0')[1]
			elif data == "elevation":
				return (serialData.split('+0')[2]).strip()
    else:
        return "Error"
		
@app.route("/sendData")
def sendData():
    # Lectura valores
    _az = request.args.get('a')
    _el = request.args.get('e')
    
    if ser.isOpen():
		ser.write('W'+_az+' '+_el)
		#ser.write('W'+_az)
		print("moviendo: az: "+_az+", el: "+_el)
		return "ok"
    else:
        return "Error"
	
if __name__ == "__main__":
    app.run(host='0.0.0.0',port=3000,debug=True)
