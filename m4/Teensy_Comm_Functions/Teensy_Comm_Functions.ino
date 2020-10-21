//Teensy code

void setup() {
  Serial1.begin(9600);
}

void loop() {
  
}
  if Serial1.available(){
    
    uint8_t opcode = Serial1.read();
    if (opcode == 0x01) {
      motionProfile = Serial1.read();
      pwmSetting = Serial1.read();
    }

}
