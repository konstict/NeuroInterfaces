int pinECG = A0;
void setup(){
  pinMode(pinECG, INPUT);
  Serial.begin(9600);
}

int sumValue = 0;
int counter = 0;
int integrated = 0;
int integratedPrev = 0;
int sumValue2 = 0;
int counter2 = 0;
int result = 0;
unsigned long prevTime = millis();
unsigned long latestPulseTime = millis();
void loop(){
  if (millis() - prevTime >= 4){
    int value = map(analogRead(pinECG), 0, 1023, 0, 255);
    counter++;
    sumValue += value;
    if (counter >= 5){
      integrated = sumValue / counter;
      counter = 0;
      sumValue = 0;
    }
    int differ = integrated - integratedPrev;
    integratedPrev = integrated;
    int squared = differ * differ;
    if (squared >= 1023) squared = 1023;
    counter2++;
    sumValue2 += squared;
    if (counter2 >= 10){
      result = sumValue2 / counter2;
      counter2 = 0;
      sumValue2 = 0;
    }
//    Serial.println(result); 
    
    if (result >= 120){
      int proshlo = millis() - latestPulseTime;
      if (proshlo >= 400){
        latestPulseTime = millis();
        Serial.println( 60000/proshlo ); 
      }
    }
    prevTime = millis();
  }
}
