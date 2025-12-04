int sensorPin0 = A0;
int sensorPin1 = A1;
int sensorValue0 = 0;
int sensorValue1 = 0;


void setup() {
  Serial.begin(9600);
}


void loop() {
  sensorValue0 = analogRead(sensorPin0);
  sensorValue1 = analogRead(sensorPin1);

  sensorValue0 = map(sensorValue0, 0, 1023, 0, 360);
  sensorValue1 = map(sensorValue1, 0, 1023, 0, 360);

  Serial.print(sensorValue0);
  Serial.print(',');
  Serial.print(sensorValue1);
  Serial.println();

  delay(1);
}