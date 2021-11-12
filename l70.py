import serial, time

SERIALPORT = "/dev/ttyUSB0"
BAUDRATE = 9600

ser = serial.Serial(SERIALPORT, BAUDRATE)
ser.bytesize = serial.EIGHTBITS #number of bits per bytes
ser.parity = serial.PARITY_NONE #set parity check: no parity
ser.stopbits = serial.STOPBITS_TWO #number of stop bits
ser.timeout = None          #block read
ser.xonxoff = False     #disable software flow control
ser.rtscts = False     #disable hardware (RTS/CTS) flow control
ser.dsrdtr = True       #disable hardware (DSR/DTR) flow control
ser.writeTimeout = 0     #timeout for write

print ("Starting Up Serial Monitor")
ser.close()

try:
    ser.dtr = False
    ser.open()
    
except Exception as e:
    print ("Exception: Opening serial port: " + str(e))

if ser.isOpen():
    try:
        ser.dtr = True
        time.sleep(2)
        ser.flushInput()
        ser.flushOutput()
        # ser.write("1\r\n".encode('ascii'))
        # print("write data: 1")
        time.sleep(0.5)
        numberOfLine = 0
        ack = [0x06,0x06,0x00]
        data = []
        while True:
            print('dtr:' + "{}".format(ser.dtr))
            print('dsr:' + "{}".format(ser.dsr))
            response = ser.read().hex()
            # response = ser.readline().decode('ascii')
            print("read data: " + response)
            data.append(response)
            if ''.join(data) == '050500':
                print ('@LM received')
                ser.write(serial.to_bytes(ack))
                data = []
            if response == '17':
                print('end of block detected')
                response = ser.read(2).hex()
                data.append(response)
                res = data[1:len(data)-2]
                res = ''.join(res)
                res = bytes.fromhex(res).decode('ASCII')
                print(f'Block:{res}\n')
                data = []
                time.sleep(0.2)
                ser.write(serial.to_bytes(ack))
            if response == '03':
                print('last block detected')
                response = ser.read(2).hex()
                data.append(response)
                # response = ser.read().hex()
                # data.append(response)
                res = data[1:len(data)-2]
                res = ''.join(res)
                res = bytes.fromhex(res).decode('ASCII')
                print(f'Block:{res}\n')
                data = []
                time.sleep(0.2)
                ser.write(serial.to_bytes(ack))
            if ''.join(data) == '040400':
                print ('EOT')
                time.sleep(0.2)
                ser.dtr = False
                time.sleep(0.5)
                print('dtr:' + "{}".format(ser.dtr))
                print('dsr:' + "{}".format(ser.dsr))
                # ser.write(serial.to_bytes(ack))
                data = []
                break
        ser.close()
    except Exception as e:
        print ("Error communicating...: " + str(e))
else:
    print ("Cannot open serial port.")
