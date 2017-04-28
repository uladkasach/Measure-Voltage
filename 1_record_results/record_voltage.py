##############
## Script listens to serial port and writes contents into a file
##############
## requires pySerial to be installed 

'''
cd /var/www/git/More/Measure-Voltage/; python3 record_voltage.py
'''


import serial


write_to_file_path = "output.txt";
output_file = open(write_to_file_path, "w+");
ser = serial.Serial('/dev/ttyACM0', 115200)
while True:
    line = ser.readline();
    line = line.decode("utf-8") # decodes line into string from bytes to write to file. If faster speed is required then writing binary would improve performance, skipping this step. 
    print(line);
    output_file.write(line);
