//Teensy code

void setup() {
  Serial1.begin(9600);
  Serial.begin(9600);
}

void loop() {
  if (Serial1.available()){
    uint8_t motionProfile;
    uint8_t pwmSetting; 
     
    uint8_t opcode = Serial1.read();
    if (opcode == 0x01) {
      motionProfile = Serial1.read();
      pwmSetting = Serial1.read();
    }
    Serial.write(opcode);
    Serial.write(motionProfile);
    Serial.write(pwmSetting);
    
  }
}
  
