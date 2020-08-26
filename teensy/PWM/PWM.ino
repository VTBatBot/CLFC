void setup() {
  // put your setup code here, to run once:
pinMode(0,OUTPUT);
pinMode(1,OUTPUT);
pinMode(2,OUTPUT);
pinMode(3,OUTPUT);
pinMode(4,OUTPUT);
pinMode(5,OUTPUT);
pinMode(6,OUTPUT);
pinMode(7,OUTPUT);
pinMode(8,OUTPUT);
pinMode(9,OUTPUT);
pinMode(14,OUTPUT);
pinMode(15,OUTPUT);
pinMode(18,OUTPUT);
pinMode(19,OUTPUT);
pinMode(22,OUTPUT);
pinMode(23,OUTPUT);

analogWriteFrequency(0,10000);
analogWriteFrequency(1,10000);
analogWriteFrequency(2,10000);
analogWriteFrequency(4,10000);
analogWriteFrequency(5,10000);
analogWriteFrequency(7,10000);
analogWriteFrequency(9,10000);
analogWriteFrequency(14,10000);
analogWriteFrequency(15,10000);
analogWriteFrequency(18,10000);
analogWriteFrequency(19,10000);
analogWriteFrequency(22,10000);
analogWriteFrequency(23,10000);

analogWriteResolution(8);
}

void loop() {
  // put your main code here, to run repeatedly:
analogWrite(0,128);
analogWrite(1,128);
analogWrite(2,128);
analogWrite(3,128);
analogWrite(4,128);
analogWrite(5,128);
analogWrite(6,128);
analogWrite(7,128);
analogWrite(8,128);
analogWrite(9,128);
analogWrite(14,128);
analogWrite(15,128);
analogWrite(18,128);
analogWrite(19,128);
analogWrite(22,128);
analogWrite(23,128);
}
