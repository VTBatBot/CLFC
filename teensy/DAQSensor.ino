// using https://github.com/Richard-Gemmell/teensy4_i2c

#include <Arduino.h>

uint8_t stopcode = 12;
void setup() {
  analogReadRes(12);
  analogReadAveraging(2);
//  pinMode(0,OUTPUT);
//  pinMode(1,OUTPUT);
}

constexpr int num_pins = 2;
constexpr int num_readings = 128; 

uint16_t readings[num_pins][num_readings] = {0};
int reading_index = 0;

void loop() {
//  digitalWrite(0,HIGH);
//  digitalWrite(1,HIGH);
  constexpr int pins[num_pins] {A4, A5};
  
  for (reading_index = 0;  reading_index < num_readings; reading_index++){
      for (auto i = 0; i < num_pins; i++) {
    readings[i][reading_index] = analogRead(pins[i]);
    }
  }
   for(int i=0;i < num_readings; i++){
      for(int j=0; j < num_pins; j++){
        Serial.print(readings[j][i]);
        Serial.print(stopcode);
      }
   }
}
