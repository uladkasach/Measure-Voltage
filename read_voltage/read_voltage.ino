
/*
  Fastest Baud Rate working on dev. arduino (arduino uno) is 115200, 1 second/115200 bits = 8.6 micro seconds / bit
*/

/////////////////////////////
// Define Setup - run every time restart button is pressed
/////////////////////////////
void setup() {
  Serial.begin(115200);
}

////////////////////////////
// Define Constants
////////////////////////////
const float MAX_VOLTAGE = 5.0;
const int READINGS_PER_OUTPUT = 100; // Note - if this value is too large, no output will be produced in serial monitor. This is likely due to memory constraints.


///////////////////////////
// Define Functions
///////////////////////////
float read_voltage(float max_voltage);
float calc_mean(float data_array[]);
float calc_stdev(float mean, float data_array[]);
void output_voltage_stats(float time_readings[], float voltage_readings[]);


//////////////////////////
// Begin Main Loop
//////////////////////////
float voltage_readings[READINGS_PER_OUTPUT] = { 0 }; // initializes all elements  to 0
float time_readings[READINGS_PER_OUTPUT] = { 0 }; // initializes all elements  to 0
int counter = -1;
void loop() {           
   counter ++;
   if(counter > READINGS_PER_OUTPUT - 1){
       counter = 0;
       output_voltage_stats(time_readings, voltage_readings);
   }
   voltage_readings[counter] = read_voltage(MAX_VOLTAGE);
   time_readings[counter] = micros();
}

////////////////////////////
// Instantiate functions
////////////////////////////
float read_voltage(float max_voltage){
    int sensorValue = analogRead(A0);
    float voltage = sensorValue * (max_voltage / 1023.0);
    //Serial.println(voltage);
    return voltage;
}
void output_voltage_stats(float time_readings[], float voltage_readings[]){
    float mean_time = calc_mean(time_readings);
    float mean = calc_mean(voltage_readings);
    float stdev = calc_stdev(mean, voltage_readings);
    float reliability = (mean - stdev)/mean; // a measure of how reliable the mean is - if standard deviation is small compared to mean, reliability is high. Otherwise, mean is not informative (reliable).
    char buffer[20];
    String str_mean_time = dtostrf(mean_time, 6, 3, buffer);
    String str_mean = dtostrf(mean, 6, 3, buffer);
    String str_stdev = dtostrf(stdev, 6, 3, buffer);
    String str_reli = dtostrf(reliability, 6, 3, buffer);
    Serial.println("mean : " + str_mean + ", stdev : " + str_stdev + ", reliability : " + str_reli+ ", time : " + str_mean_time);
}
float calc_mean(float data_array[]) {
    float mean, sum = 0.0;
    for (int i = 0; i < READINGS_PER_OUTPUT; ++i) {
        sum += data_array[i];
    }
    mean = (sum / READINGS_PER_OUTPUT);
    return mean;
}
float calc_stdev(float mean, float data_array[]){
    float SSE, variance, stdev = 0.0;
    for (int i = 0; i < READINGS_PER_OUTPUT; ++i) {
        SSE += (data_array[i] - mean)*(data_array[i] - mean);
    }
    variance = (SSE / READINGS_PER_OUTPUT);
    stdev = sqrt(variance);
    return stdev;
}
