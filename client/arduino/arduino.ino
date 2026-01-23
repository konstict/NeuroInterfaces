void setup() {
  pinMode(A0, INPUT);
  Serial.begin(9600);
}

unsigned long lastTime = millis();
unsigned long lastTimePulse = millis();

int sumValue = 0;
int sumSum = 0;
int sumCounter = 0;
int sumValuePrev = 0;

int sumValue2 = 0;
int sumSum2 = 0;
int sumCounter2 = 0;

void loop() {
  if (millis()- lastTime >= 5){
    int value = map(analogRead(A0), 0, 1024, 0, 255);

    sumSum = sumSum + value;
    sumCounter++;
    if (sumCounter >= 5){
      sumValue = sumSum / sumCounter;
      sumSum = 0;
      sumCounter = 0;
    }

    int diff = sumValue - sumValuePrev;
    sumValuePrev = sumValue;
    int newDiff = diff * diff;

    sumSum2 = sumSum2 + newDiff;
    sumCounter2++;
    if (sumCounter2 >= 5){
      sumValue2 = sumSum2 / sumCounter2;
      sumSum2 = 0;
      sumCounter2 = 0;
    }

    if (sumValue2 >= 500){
      if (millis() - lastTimePulse >= 400){
        Serial.println(60000 / (millis() - lastTimePulse));
        lastTimePulse = millis();
      }
    }
    // Serial.println(value);

    lastTime = millis();
  }
}
