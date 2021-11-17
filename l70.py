# test L70
import serial, time, re, json
from datetime import datetime
from string import Template
from pathlib import Path

LM_FOLDER = '/machines/cv5000/lm/'

now = datetime.now()

# useful
# remove STX start txt and EOT/EOB end of txt or block and checksum
def hexToAscii(blocklst):
    return bytes.fromhex(''.join(blocklst[1:len(blocklst)-2])).decode('ASCII')

mesDict = {'R': [], 'L' : [], 'pd': {}}
info_json = { 'machine': '', 'status': 'processing', 'error': '', 'data': {} }

def checkMachine(asciiBlock):
    p = re.compile('@(?P<machine>\w\w)')
    m = p.search(asciiBlock)
    if m != None:
        info_json['machine']=m.group('machine')
        return True
    else:
        return False

# format _R/L+/-00.00+/-00.00000 eg _R+01.25-0.25165
def checkRx(asciiBlock):
    p = re.compile('([\ ])(?P<side>[LR])(?P<sph>(\+|-)\d\d.\d\d)(?P<cyl>(\+|-)\d\d.\d\d)(?P<axis>\d\d\d)')
    m = p.search(asciiBlock)
    if m != None:
        res = {'type' : 'rx', 'sph': m.group('sph'), 'cyl': m.group('cyl'), 'axis': m.group('axis') }
        mesDict[m.group('side')].append(res)
        return True
    else:
        return False

def checkAdd(asciiBlock):
    p = re.compile('A(?P<side>[LR])(?P<add>(\+|-)\d\d.\d\d)')
    m = p.search(asciiBlock)
    if m != None:
        res = {'type' : 'add', 'add': m.group('add')}
        mesDict[m.group('side')].append(res)
        return True
    else:
        return False

def checkPrism(asciiBlock):
    p = re.compile('P(?P<side>[LR])I(?P<U>\d\d.\d\d)U(?P<I>\d\d.\d\d)')
    m = p.search(asciiBlock)
    if m != None:
        res = {'type' : 'prism', 'U': m.group('U'), 'I': m.group('I')}
        mesDict[m.group('side')].append(res)
        return True
    else:
        return False

def checkPd(asciiBlock):
    p = re.compile('PD(?P<B>\d\d.\d)(?P<R>\d\d.\d)(?P<L>\d\d.\d)')
    m = p.search(asciiBlock)
    if m != None:
        mesDict['pd']= m.group('B')
        mesDict['R'].append({'pd' : m.group('R')})
        mesDict['L'].append({'pd' : m.group('L')})
        return True
    else:
        return False

# init serial link
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
        time.sleep(0.2)
        ser.flushInput()
        ser.flushOutput()
        time.sleep(0.2)
        ack = [0x06,0x06,0x00]
        data = []
        fullstr = ''
        print('Listening rs232...')
        info_json['status'] = 'Listening rs232...'
        # send ack in case L70 already started handshake
        ser.write(serial.to_bytes(ack))
        while True:
            response = ser.read().hex()
            # print("read data: " + response)
            data.append(response)
            # shakehand 
            if ''.join(data) == '050500':
                info_json['status'] = '@LM received'
                info_json['dtr'] = str(ser.dtr)
                info_json['dsr'] = str(ser.dsr)
                ser.write(serial.to_bytes(ack))
                data = []
            if response == '17':
                info_json['status'] = 'end of block detected'
                response = ser.read(2).hex()
                data.append(response)
                info_json['dtr'] = str(ser.dtr)
                info_json['dsr'] = str(ser.dsr)
                asciiBlock = hexToAscii(data)
                fullstr += asciiBlock
                # print(f'{asciiBlock}')
                checkMachine(asciiBlock) 
                checkRx(asciiBlock) 
                checkAdd(asciiBlock)
                checkPrism(asciiBlock)
                checkPd(asciiBlock)
                data = []
                time.sleep(0.02)
                ser.write(serial.to_bytes(ack))
            if response == '03':
                info_json['status'] = 'last block detected'
                response = ser.read(2).hex()
                data.append(response)
                info_json['dtr'] = str(ser.dtr)
                info_json['dsr'] = str(ser.dsr)
                asciiBlock = hexToAscii(data)
                fullstr += asciiBlock
                # print(f'{asciiBlock}')
                checkRx(asciiBlock) 
                checkAdd(asciiBlock)
                checkPrism(asciiBlock)
                checkPd(asciiBlock)
                checkRx(asciiBlock)
                data = []
                time.sleep(0.02)
                ser.write(serial.to_bytes(ack))
            if ''.join(data) == '040400':
                info_json['status'] = 'EOT'
                info_json['dtr'] = str(ser.dtr)
                info_json['dsr'] = str(ser.dsr)
                time.sleep(0.2)
                ser.dtr = False
                time.sleep(0.2)
                info_json['dtr'] = str(ser.dtr)
                info_json['dsr'] = str(ser.dsr)
                # print(f'dtr:{ser.dtr}')
                # print(f'dsr:{ser.dsr}')
                data = []
                info_json['data']= mesDict
                print(json.dumps(info_json))
                # write file
                nsLM = Path('topconlm_temp.xml').read_text()
                tempDict = { 
                    "sphR": mesDict['R'][0]['sph'],
                    "cylR": mesDict['R'][0]['cyl'],
                    "axisR": mesDict['R'][0]['axis'],
                    "add1R": mesDict['R'][1]['add'],
                    "HpR": mesDict['R'][2]['U'],
                    "VpR": mesDict['R'][2]['I'],
                    "pdR": mesDict['R'][3]['pd'],
                    "sphL": mesDict['L'][0]['sph'],
                    "cylL": mesDict['L'][0]['cyl'],
                    "axisL": mesDict['L'][0]['axis'],
                    "add1L": mesDict['L'][1]['add'],
                    "HpL": mesDict['L'][2]['U'],
                    "VpL": mesDict['L'][2]['I'],
                    "pdL": mesDict['L'][3]['pd'],
                    }
                t = Template(nsLM).safe_substitute(tempDict)
                filename = f'M-SERIAL4174_{now.strftime("%Y%m%d")}_{now.strftime("%H%M%S%f")}_TOPCON_CL300_00.xml'
                try:                    
                    with open(LM_FOLDER+filename,'w') as file:
                        file.write(t)
                except Exception as e:
                    print('error:',str(e))
                # reset link
                mesDict = {'R': [], 'L' : [], 'pd': {}}
                info_json = { 'machine': '', 'status': 'processing', 'error': '', 'data': {} }
                ser.dtr = True
                time.sleep(0.2)
                ser.flushInput()
                ser.flushOutput()
                time.sleep(0.2)
        ser.close()
        print('Connection closed')
        info_json['status'] = 'Connection closed'
        # print(fullstr)
        info_json['data']= mesDict
        print(json.dumps(info_json))

    except Exception as e:
        info_json['error'] = str(e)
        print(json.dumps(info_json))
else:
    print ("Cannot open serial port.")
    info_json['status'] = 'Error'
    info_json['error'] = 'Cannot open serial port'
    print(json.dumps(info_json))