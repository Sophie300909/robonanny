String message;
String commands[5];
int buzzerPin = 8;
#include <Servo.h>
Servo myservo;
int j;

void setup() {
  Serial.begin(9600);
  Serial.setTimeout(100);
  Serial.println("READY: Servo controller started");
  pinMode(9, OUTPUT);
  pinMode(10, OUTPUT);
  pinMode(buzzerPin, OUTPUT);
  myservo.attach(10);
  myservo.write(0);
}

void loop() {
  if (Serial.available() > 0)
  {
    message = Serial.readStringUntil('\n');
    for (int i = 0; i < 5; i++) {
      commands[i] = message;
      message = Serial.readStringUntil('\n');
      Serial.println(commands[i]);
    }
  }
  if (commands[1] == "yes_l") {
    digitalWrite(9, HIGH);
  }
  if (commands[1] == "no_l") {
    digitalWrite(9, LOW);
  }
  if (commands[4] == "yes_s") {
    digitalWrite(10, HIGH);
    for (int i = 0; i <= 90; i++) {
      myservo.write(i);
      j=i;
      delay(20);

    }
    for (j; j>=0; j--){
      myservo.write(j);
      delay(20);
    }
  }
  if (commands[4] == "no_s") {
    digitalWrite(10, LOW);
  }
  if (commands[0] == "yes_c") {
    playNote(262, 400);
    playNote(440, 400);
    playNote(440, 400);
    playNote(392, 400);
    playNote(440, 400);
    playNote(349, 400);
    playNote(262, 400); 
    playNote(262, 400);
    playNote(262, 400);
    playNote(440, 400);
    playNote(440, 400);
    playNote(466, 400);
    playNote(392, 400);
    playNote(523, 600);
    playNote(0, 20);
    playNote(523, 400);
    playNote(294, 400);
    playNote(294, 400);
    playNote(466, 400);
    playNote(466, 400);
    playNote(440, 400);
    playNote(392, 400);
    playNote(349, 400);
    playNote(262, 400);
    playNote(440, 400);
    playNote(440, 400);
    playNote(392, 400);
    playNote(440, 400);
    playNote(349, 600);
    
    delay(2000);
  }
  if (commands[0] == "no_c") {
      noTone(buzzerPin);
  }
}

void playNote(int frequency, int duration) {
  tone(buzzerPin, frequency);
  delay(duration);
  noTone(buzzerPin);
  delay(50);
}