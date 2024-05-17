# Import the libraries
import serial
import datetime
import pytz
import requests
import json

# set time zone for time stamp
fullMoonTimeZone = pytz.timezone('America/Chicago')

# URL for fastAPI that is connected to our mongodb instance
url = 'http://192.168.3.54:8000/records/'

# Try to connect to the port
print('ready to try to connect')
# an array to store bytes of information from serial communication
message = []

# handle serial connections to plc
try:
    # Using COM4 as incoming serial port connection, replace with yours.
    plcPySerial = serial.Serial('COM3', 9600)
    print('serial connected to com3')
except:
    print('Failed to connect. Try running this command in the command line to see your available serial port connections:')
    print('python -m serial.tools.list_ports')
    print('(Note that this is not your command line, this is a the Python Interpreter)')
    # stops program on failure
    exit()

try:
    # Using COM4 as outgoing serial port connection, replace with yours.
    arduinoPySerial = serial.Serial('COM4', 9600)
    print('serial connected to com4')
except:
    print('Failed to connect. Try running this command in the command line to see your available serial port connections:')
    print('python -m serial.tools.list_ports')
    print('(Note that this is not your command line, this is a the Python Interpreter)')
    # stops program on failure
    exit()


# Read data and print it to terminal... until you stop the program
while 1:
    # reads a line of serial data, it expects a line ending
    x = plcPySerial.read()
    # remove irrelevant null byte from array
    byte = x.decode('utf-8').rstrip('\x00')
    if byte != '':
        # if byte is our defined end char keep adding to array
        if byte != '>':
            message.append(byte)
        if byte == '>':
            # transforms byte array into string for debug message
            command = (''.join(message)+'>')

            print('sending command')
            print(command)
            # sends serial command to Arduino as byte array
            arduinoPySerial.write(command.encode())
            # checks if message is to be posted to mongodb database for score keeping
            if message[0] == 'b':
                # parse array for time information and change it to an int
                time = message[1:5]
                timeStr = ''.join(time)
                timeInt = int(timeStr)
                # parse array for hint information and change it to an int
                hints = message[5:7]
                hintsStr = ''.join(hints)
                hintsInt = int(hintsStr)
                # applies math for score calculation
                timeInRoom =  4200 - timeInt - (hintsInt * 180)
                #finalTimeMinutes = timeInRoom // 60
                #finalTimeSeconds = timeInRoom - finalTimeMinutes * 60
                #finalTimeString = str(finalTimeMinutes) + ":" + str(finalTimeSeconds)
                finalTimeString = str(datetime.timedelta(seconds=timeInRoom))
                print(finalTimeString)
                print('hits int calc:'+str( hintsInt * 180))

                if (timeInt > 600):
                    score = ((timeInt - 600) * 150) + 10000
                else:
                    score = 10000                
                
                try:
                    # use datetime to generate timestamp and time of database posting
                    timeStamp = datetime.datetime.now(
                        fullMoonTimeZone).strftime("%H:%M:%S")
                    date = datetime.datetime.now(
                        fullMoonTimeZone).strftime("%m/%d/%Y")

                    data = {
                        "teamName": "anonymous",
                        "dateOfGame": date,
                        "escapeTime": timeInt,
                        "hintsUsed": hintsInt,
                        "score": score,
                        "timeGameComplete": timeStamp,
                        "timeInRoom": finalTimeString
                    }
                    print(data)
                    # Convert data to JSON format
                    json_data = json.dumps(data)

                    # Set the Content-Type header to application/json
                    headers = {'Content-Type': 'application/json'}

                    # Send POST request with JSON data
                    if (timeInRoom > 1200):
                        response = requests.post(
                            url, data=json_data, headers=headers)

                    # Print the response
                    print(response.json())
                    print('post success :)')

                except:
                    print('failed to post :(')
            # sets command and message back to blank values to await next serial message
            command = None
            message = []
