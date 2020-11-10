
#include <Servo.h> 
 
Servo leftservo;  //Left servo object variable 
Servo rightservo; //Right servo object variable

int pos = 0;    // variable to store the servo position 
 
void setup() 
{ 
  leftservo.attach(8); // attaches the left servo on pin 8 to the servo object 
  rightservo.attach(9); //attaches the right servo on pin 9 to the servo object
} 
 
void loop() 
{ 
  for(pos = 0; pos <= 180; pos += 1) // goes from 0 degrees to 180 degrees 
  {                                  // in steps of 1 degree 
    leftservo.write(pos);            // tell left servo to go to position in variable 'pos' 
    rightservo.write(pos);           // tell right servo to go to position in variable 'pos'
    delay(10);                       // waits 15ms for the servo to reach the position 
  } 
  for(pos = 180; pos>=0; pos-=1)  // goes from 180 degrees to 0 degrees 
  {                               
    leftservo.write(pos);         // tell left servo to go to position in variable 'pos' 
    rightservo.write(pos);        // tell right servo to go to position in variable 'pos'
    delay(10);                    // waits 15ms for the servo to reach the position 
  } 
}

void setmovement(){
unsigned char byteservo = 0x50; //What should byteservo represent?
opcode = serial.read()
  if (byteservo & 0x40)
  {
    rightservo == true;
    if (byteservo & 0x80)
    {
      leftservo == true;
    }
    ValueByte = 0x3F && byteservo ;
    value = int(ValueByte);
    Angle = (180/64)*value;
  }
}
