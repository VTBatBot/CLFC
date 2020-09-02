// VT BIST BatLab 2020, 09/02/2020
// Code written by Nick Gammon (http://www.gammon.com.au/forum/?id=10892&reply=1#reply1), modified by Nathan Cox

// This code turns an Arduino UNO into a SPI Slave device that recieves info via SPI and relays it to the 
// serial monitior using Serial (i.e. the USB cable)...

// MAKE SURE TO SET THE SERIAL MONITOR TO 115200 BAUD TO READ THE INFO BEING SENT!!!

#include <SPI.h>

char buf [100];
volatile byte pos;
volatile boolean process_it;

void setup (void)
{
  Serial.begin (115200);   // debugging
  
  // turn on SPI in slave mode
  SPCR |= bit (SPE);

  // have to send on master in, *slave out*
  pinMode(MISO, OUTPUT);
  
  // get ready for an interrupt 
  pos = 0;   // buffer empty
  process_it = false;

  // now turn on interrupts
  SPI.attachInterrupt();

}  // end of setup


// SPI interrupt routine
ISR (SPI_STC_vect)
{
byte c = SPDR;  // grab byte from SPI Data Register
  
  // add to buffer if room
  if (pos < (sizeof (buf) - 1))
    buf [pos++] = c;
    
  // example: newline means time to process buffer
  if (c == '\n')
    process_it = true;
      
}  // end of interrupt routine SPI_STC_vect

// main loop - wait for flag set in interrupt routine
void loop (void)
{
  if (process_it)
    {
    buf [pos] = 0;  
    Serial.println (buf);
    pos = 0;
    process_it = false;
    }  // end of flag set
    
}  // end of loop

