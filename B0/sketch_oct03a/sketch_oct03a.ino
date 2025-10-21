int ecg = A0;
void setup() {
  Serial.begin(9600);
  pinMode(ecg, INPUT);
}

int counter = 0;
int sumSensorValue = 0;
int latestAvgSensorValue = 0;
void loop() {
  int sensorValue = map(analogRead(ecg), 0, 1023, 0, 255);
  
//  counter++;
//  sumSensorValue += sensorValue;
//  if (counter > 3){
//    latestAvgSensorValue = sumSensorValue/counter;
//    counter = 0;
//    sumSensorValue = 0;
//    Serial.println(latestAvgSensorValue);
//  }
  Serial.println(sensorValue);
}
