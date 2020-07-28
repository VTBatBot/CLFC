#include <Adafruit_TLC5947.h>

#include <stdio.h>

//Number of TLC5947 chained
#define quant_tlc 1
// Digital pin connected to the TLC5947's LAT
#define latch_pin 5
// Digital pin connected to the TLC5947's CLK
#define clock_pin 6
// Digital pin connected to the TLC5947's DIN
#define din_pin 7

Adafruit_TLC5947 tlc = Adafruit_TLC5947(quant_tlc, clock_pin, din_pin, latch_pin);

// Total number of channels supported by the TLC5947
int const num_channels = 24;
// Total number of channels utilized by each profile
int const num_used_channels = 12;

void setup() {
  //This was from Brandon's code tlc5947_demo.ino
  //This is required for the m4 to send output signals through these pins
  pinMode(latch_pin, OUTPUT);
  pinMode(clock_pin, OUTPUT);
  pinMode(din_pin, OUTPUT);

  //This starts the serial transfer of data
  Serial.begin(9600);
  while(!Serial);
  Serial.println("TLC5974 test");

  //Required for the tlc5948
  tlc.begin();
}

void loop() {
  // put your main code here, to run repeatedly:
  static int count = 0;

  uint16_t pwm;

  if (!count)
  for (uint8_t channel = 0; channel < num_used_channels; channel++){ // runs the loop for each channel used
    tlc.setPWM(channel, pwm = 0); //
    tlc.write();
  }

  count++; 
}
