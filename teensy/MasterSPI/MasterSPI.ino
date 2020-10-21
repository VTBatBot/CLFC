#include <SPI.h>


//#define FLASH_SS1 10 //FLASH_SS is pin 10
//#define MiSo1 9 //MISO is pin 9
//#define MoSi1 8 //MOSI is pin 8

void setup (void)
{

  digitalWrite(53, HIGH);  // ensure FLASH_SS stays high for now

  // Put SCK, MOSI, FLASH_SS pins into output mode
  // also put SCK, MOSI into LOW state, and SS into HIGH state.
  // Then put SPI hardware into Master mode and turn SPI on
  SPI.begin ();

  // Slow down the master a bit
  SPI.setClockDivider(SPI_CLOCK_DIV8);
 
}  // end of setup


void loop (void)
{

  char c;

  // enable Slave Select
  digitalWrite(53, LOW);    // FLASH_SS is pin 10

  // send test string
  for (const char * p = "Hello, world!\n" ; c = *p; p++)
    SPI.transfer (c);

  // disable Slave Select
  digitalWrite(53, HIGH);

  delay (1000);  // 1 seconds delay
}  // end of loop
