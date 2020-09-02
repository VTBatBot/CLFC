//SPI slave code from Github provided by Patrick
#include <SPI.h>
char buf [100];
volatile byte pos;
volatile boolean process_it;
void setup() {
//setup SPI interrupt
Serial.begin (115200);   // debugging

// have to send on master in, *slave out*
pinMode(MISO, OUTPUT);

// turn on SPI in slave mode
SPCR |= _BV(SPE);

// get ready for an interrupt
pos = 0;   // buffer empty
process_it = false;

// now turn on interrupts
SPI.attachInterrupt();
// Setting up pinmode for output
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

//setting PWM frequency
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

//Provides 256 levels of Duty cycle control
analogWriteResolution(8);

}
// SPI interrupt routine
ISR (SPI_STC_vect)
{
byte c = SPDR;  // grab byte from SPI Data Register

  // add to buffer if room
  if (pos < sizeof buf)
    {
    buf [pos++] = c;

    // example: newline means time to process buffer
    if (c == '\n')
      process_it = true;

    }  // end of room available
}  // end of interrupt routine SPI_STC_vect
void loop() {
//Case statement for whether PWM is on or off
enum {ON,OFF} OnOff=OFF;
switch(OnOff)
{
  case ON:
  //output PWM at 50% duty cycle
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
  break;

  case OFF:
  //turns off PWM if there is no interrupt
  analogWrite(0,0);
  analogWrite(1,0);
  analogWrite(2,0);
  analogWrite(3,0);
  analogWrite(4,0);
  analogWrite(5,0);
  analogWrite(6,0);
  analogWrite(7,0);
  analogWrite(8,0);
  analogWrite(9,0);
  analogWrite(14,0);
  analogWrite(15,0);
  analogWrite(18,0);
  analogWrite(19,0);
  analogWrite(22,0);
  analogWrite(23,0);
  break;
}
  if (process_it)
      {

      OnOff = ON;
      buf [pos] = 0;
      Serial.println (buf);
      pos = 0;
      process_it = false;
      }  // end of flag set
    else{
      OnOff= OFF;

    }
}
