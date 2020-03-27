#include <Wire.h>

int const slave_address = 0x08;

int const num_pins = 10;
int const num_readings = 128;
int const packet_size = sizeof(uint16_t) * num_pins * num_readings;

void setup() {
  Wire.begin();
}

void loop() {
  Wire.requestFrom(slave_address, packet_size);

  for (auto i = 0; i < packet_size; i += sizeof(uint16_t)) {
    uint16_t reading = Wire.read();
    reading |= (Wire.read() << 8);

    auto pin = (i % (sizeof(uint16_t) * num_pins)) / sizeof(uint16_t);
    auto num = i / (sizeof(uint16_t) * num_pins);

    // ...
  }
}
