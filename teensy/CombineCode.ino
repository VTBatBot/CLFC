#include <Servo.h> 
 
Servo leftservo;  //Left servo object variable 
Servo rightservo; //Right servo object variable
int pos = 0;    // variable to store the servo position 

//defines pins for left stepper motors
const int LstepPin = 2;  //PUL -Pulse
const int LdirPin = 3; //DIR -Direction
const int LenPin = 4;  //ENA -Enable
//defines pins for right stepper motors
const int RstepPin = 5;  //PUL -Pulse
const int RdirPin = 6; //DIR -Direction
const int RenPin = 7;  //ENA -Enable
 
void setup() 
{ 
  leftservo.attach(8); // attaches the left servo on pin 8 to the servo object 
  rightservo.attach(9); //attaches the right servo on pin 9 to the servo object

  pinMode(LstepPin,OUTPUT); 
  pinMode(LdirPin,OUTPUT);
  pinMode(LenPin,OUTPUT);
  digitalWrite(LenPin,LOW);

  pinMode(RstepPin,OUTPUT); 
  pinMode(RdirPin,OUTPUT);
  pinMode(RenPin,OUTPUT);
  digitalWrite(RenPin,LOW);
} 
 
//Movement of left servo
void leftservo(pos)
{
  for(pos = 0; pos <= 180; pos += 1) // goes from 0 degrees to 180 degrees 
  {                                  // in steps of 1 degree 
    leftservo.write(pos);            // tell left servo to go to position in variable 'pos' 
    delay(10);                       // waits 15ms for the servo to reach the position 
  }
  for(pos = 180; pos>=0; pos-=1)  // goes from 180 degrees to 0 degrees 
  {                               
    leftservo.write(pos);         // tell left servo to go to position in variable 'pos' 
    delay(10);                    // waits 15ms for the servo to reach the position 
  } 
}

//Movement of right servo
void rigthservo(pos)
{
  for(pos = 0; pos <= 180; pos += 1) // goes from 0 degrees to 180 degrees 
  {                                  // in steps of 1 degree 
    rightservo.write(pos);            // tell left servo to go to position in variable 'pos' 
    delay(10);                       // waits 15ms for the servo to reach the position 
  }
  for(pos = 180; pos>=0; pos-=1)  // goes from 180 degrees to 0 degrees 
  {                               
    rightservo.write(pos);         // tell left servo to go to position in variable 'pos' 
    delay(10);                    // waits 15ms for the servo to reach the position 
  } 
}

//Movement of left stepper motor
void leftstepper()
{
  //Enables the motor direction to move
  digitalWrite(LdirPin,HIGH);
  //Makes 200 Pulses for making one full cycle rotation
  for(int x = 0; x < 200; x++){
    digitalWrite(LstepPin,HIGH); 
    delayMicroseconds(500); 
    digitalWrite(LstepPin,LOW); 
    delayMicroseconds(500); 
  }
  
  //One second delay 
  delay(1000);

  //Changes the rotations direction
  digitalWrite(LdirPin,LOW);
  // Makes 200 pulses for making one full cycle rotation
  for(int x = 0; x < 200; x++) {
    digitalWrite(LstepPin,HIGH);
    delayMicroseconds(500);
    digitalWrite(LstepPin,LOW);
    delayMicroseconds(500);
  }
  
  //One second delay
  delay(1000); 
}

//Movement of right stepper motor
void rightstepper()
{
  //Enables the motor direction to move
  digitalWrite(RdirPin,HIGH);
  //Makes 200 Pulses for making one full cycle rotation
  for(int x = 0; x < 200; x++){
    digitalWrite(RstepPin,HIGH); 
    delayMicroseconds(500); 
    digitalWrite(RstepPin,LOW); 
    delayMicroseconds(500); 
  }
  
  //One second delay
  delay(1000);

  //Changes the rotations direction
  digitalWrite(RdirPin,LOW);
  // Makes 200 pulses for making one full cycle rotation
  for(int x = 0; x < 200; x++) {
    digitalWrite(RstepPin,HIGH);
    delayMicroseconds(500);
    digitalWrite(RstepPin,LOW);
    delayMicroseconds(500);
  }
  //One second delay
  delay(1000); 
}

void loop() 
{ 
  uint8_t opcode = serial.read();
  uint8_t byteservo = serial.read();
  if (opcode == 0x02) {
    if (byteservo & 0x40){
      uint8_t valueB = 0x3F && byteservo;
      value = int(valueB)
      int angle = (180/64)*value
      void rightservo(angle)
    }
    if (byteservo & 0x80 {
      uint8_t valueB = 0x3F && byteservo;
      value = int(valueB)
      int angle = (180/64)*value
      void leftservo(angle)
    }
  }
}
