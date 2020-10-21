#include "Arduino.h"


//int led=13; used for testing

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
/*pinMode(led, OUTPUT);
Serial.begin(9600);used for testing */
}
void BitBash(unsigned char Byte1, unsigned char Byte2)
{

  int Byte2Val=Byte2;
  unsigned char Pin_Byte=Byte1;
  //Serial.println(Pin_Byte); used for testing
  int freq= (Byte2Val*100)+10000;
  double period = 1000000 / freq;//converts freuqency to period for delay  
  int onFor = period/2;//assumes 50% duty cycle always
  int len = 8;
  byte Comp= 1;
  int PinNum= 0;
  for(int i=0;i<len;i++)//determinest the number of active bits through comparing a shifted 1 
  {    
    if(Pin_Byte & Comp)
    {
      PinNum++;
    }
    Comp<<=1;
  }
  int PinOn[PinNum]={};
  int PinOff[PinNum]={};
  PinNum=0;
  Comp= 1;


  for(int i=0;i<len;i++)//this sets the values of the pins that will be turned on
  {
    if(Pin_Byte & Comp)
    {

      PinOn[PinNum]=i;
      if (i == 0)
      {
     PinOff[PinNum]=8;
      }
      else if (i ==1)
      {
      PinOff[PinNum]=9;
      }
      else if (i ==2)
      {
      PinOff[PinNum]=14;
      }
      else if (i ==3)
      {
      PinOff[PinNum]=15;
      }
      else if (i ==4)
      {
      PinOff[PinNum]=18;
      }
      else if (i ==5)
      {
      PinOff[PinNum]=19;
      }
      else if (i ==6)
      {
      PinOff[PinNum]=22;
      }
      else if (i ==7)
      {
      PinOff[PinNum]=23;
      }
      PinNum++;
    }

    Comp <<=1;
  }

   for (int j=0; j<150; j++)//**pulses for 150 cycles to inflate and can be adjusted through testing**
    {
    for(int i=0;i<PinNum;i++)//activates pins that were set high for this instance
      {
      digitalWrite(PinOn[i],HIGH);
      }
      delayMicroseconds(onFor);     
     for(int i=0;i<PinNum;i++)
      {
      digitalWrite(PinOn[i],LOW);
      }     
      delayMicroseconds(onFor);     
    }
    for (int j=0; j<150; j++)//**pulses for 150 cycles to deflate and can be adjusted through testing**
    {
      for(int i=0;i<PinNum;i++)//activates pins that were set high for this instance
      {
        digitalWrite(PinOff[i],HIGH);
      }
        delayMicroseconds(onFor);
      
       for(int i=0;i<PinNum;i++)
      {
        digitalWrite(PinOff[i],LOW);
      }
        delayMicroseconds(onFor);
    }
   return;
}
void loop() {
  // put your main code here, to run repeatedly:
byte Byte1=0x0f;//this determines the active pins, each bit of a byte relates to an actuator
unsigned char Byte2=0xff;//this determins the frequency, 0x00=10KHz - 0xff=35.5KHz increasing the value of the byte by 1 increases the PWM frequency by 100Hz
BitBash(Byte1,Byte2);//function call

}
