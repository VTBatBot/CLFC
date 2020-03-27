// Digital pin connected to the TLC5947's LAT
int const latch_pin = 5;
// Digital pin connected to the TLC5947's CLK
int const clock_pin = 6;
// Digital pin connected to the TLC5947's DIN
int const din_pin = 7;

// Total number of channels supported by the TLC5947
int const num_channels = 24;
// Total number of channels utilized by each profile
int const num_used_channels = 12;

// List of all PWM profiles: each row begins with the number of milliseconds
// to hold it, followed by 12-bit values for each PWM channel
uint16_t pwm_buffer[][1 + num_used_channels] = {
  { 500,     0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0 },
  { 500,     0, 4095,    0, 4095,    0, 4095,    0, 4095,    0, 4095,    0, 4095 },
  { 500,  4095,    0, 4095,    0, 4095,    0, 4095,    0, 4095,    0, 4095,    0 },
  {   0,     0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0 }
};

// Number of profiles (rows) in pwm_buffer
int const num_profiles = sizeof(pwm_buffer)/sizeof(pwm_buffer[0]);

// Index into pwm_buffer of the current PWM profile
int current_profile = 0;

// Time of the last profile change
int last_update = 0;

// Send a PWM profile to the TLC5947
void write_pwm_buffer(uint16_t *buffer, int channels = num_channels) {
  digitalWrite(latch_pin, LOW);

  for (auto ch = 0; ch < num_channels; ch++) {
    uint16_t value = (ch >= channels) ? 0 : buffer[ch];

    for (auto bit = 12 - 1; bit >= 0; bit--) {
      digitalWrite(clock_pin, LOW);

      digitalWrite(din_pin, (value & (1 << bit)) ? HIGH : LOW);

      digitalWrite(clock_pin, HIGH);
    }
  }

  digitalWrite(clock_pin, LOW);

  digitalWrite(latch_pin, HIGH);
  digitalWrite(latch_pin, LOW);
}

void setup() {
  pinMode(latch_pin, OUTPUT);
  pinMode(clock_pin, OUTPUT);
  pinMode(din_pin, OUTPUT);

  // Apply the current 
  write_pwm_buffer(&pwm_buffer[current_profile][1], num_used_channels);
}

void loop() {
  auto now = millis();
  
  // Check if the next profile needs to be applied
  auto profile_finished = now - last_update > pwm_buffer[current_profile][0];
  auto last_profile = current_profile == num_profiles - 1;
  if (profile_finished && !last_profile) {
    current_profile++;

    write_pwm_buffer(&pwm_buffer[current_profile][1], num_used_channels);
  }
}
