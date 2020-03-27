// using https://github.com/Richard-Gemmell/teensy4_i2c

#include <Arduino.h>
#include <i2c_driver.h>
#include <i2c_driver_wire.h>

void setup() {
  analogReadRes(12);
  analogReadAveraging(2);

  Wire.begin(0x08);
  Wire.onRequest(handle_i2c);
}

constexpr int num_pins = 10;
constexpr int num_readings = 128;

uint16_t readings[num_pins][num_readings] = {0};
int reading_index = 0;

void loop() {
  constexpr int pins[num_pins] { A0, A1, A2, A3, A4, A5, A6, A7, A8, A9 };
  
  for (auto i = 0; i < num_pins; i++) {
    readings[i][reading_index] = analogRead(pins[i]);
  }

  reading_index = (reading_index + 1) % num_readings;
}

void handle_i2c() {
	Wire.write(reinterpret_cast<uint8_t *>(readings),
		sizeof(uint16_t) * num_pins * num_readings);
}
