void setup() { // при запуске, инициализация порта и Serial (для print)
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

void loop() { // главный цикл в ардуино (вызывается каждый тик)
  if (millis() - lastTime >= 5){ // установка точного кд в 5 миллисекунд
    int value = map(analogRead(A0), 0, 1024, 0, 255); // получаем значение и переводим границы в 0-255

    sumSum = sumSum + value; // для усреднения значений - суммируем их
    sumCounter++; // считаем количество суммирования
    if (sumCounter >= 5){ // находим среднее арифметическое значение и обнуляем переменные
      sumValue = sumSum / sumCounter;
      sumSum = 0;
      sumCounter = 0;
    }

    int diff = sumValue - sumValuePrev; // операция дифференцирования
    sumValuePrev = sumValue; // находим разность между текущим значением и предыдущим
    int newDiff = diff * diff; // берём в квадрат

    sumSum2 = sumSum2 + newDiff; // повторяем взятие усреднённых значений
    sumCounter2++;
    if (sumCounter2 >= 5){
      sumValue2 = sumSum2 / sumCounter2;
      sumSum2 = 0;
      sumCounter2 = 0;
    }

    if (sumValue2 >= 500){ // 500 - константа, значение выше или равно константе - можем регнуть удар
      if (millis() - lastTimePulse >= 400){ // если с предыдущего удара сердца прошло более или равно 0.4 секунд, то
        Serial.println(60000 / (millis() - lastTimePulse)); // находим и регаем пульс (количество ударов в минуту)
        lastTimePulse = millis(); // записываем время последнего удара
      }
    }
    // Serial.println(value);

    lastTime = millis(); // итерация цикла завершена, записываем время его конца
  }
}
