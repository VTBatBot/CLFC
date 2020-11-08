void setup() {
  // put your setup code here, to run once:
Serial1.begin(9600);
}

void loop() {
  // put your main code here, to run repeatedly:
Serial1.write(0x01);
Serial1.write(0xff);
Serial1.write(0x80);
}
