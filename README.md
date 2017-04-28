# MeasureVoltage
Measure voltage with an arduino, record the data returned, and analyze the data.


### Measure Data
`0_measure_data` contains arduino scripts relating to data measurement.

`read_voltage` runs on arduino and measures the voltage on pin A0.
  - note: arduino measures voltages between `0-5V`. If voltages greater than that are desired, a voltage divider must be made and the 'divided' voltage should be inputted to this pin.
    - in this case, do not forget to change the value of `MAX_VOLTAGE` in the `read_voltage.ino` file.
    
### Record Data
`1_record_data` contains python scripts, set to run on your PC, to record the data.

`record_voltage.py` is a simple python script that listens to the serial port the arduino is connected to and writes the content to a text file.
  - this is essentially what the Arduino IDE's `serial monitor` does, except it additionally writes the content to a file.

### Analyze Data
`2_analyze_data` contains python scripts which can:
    - Detect when voltage increases, plateus, and decreases
    - Can calculate capacitance from discharge of capacitor (decrease in voltage) - if this is used to measure capacitance. 


### Extra
The current configuration records mean and stdev of 100 voltage measurements, every 22.8 milliseconds, on a Arduino Uno.
