These two codes are meant to be used to test SPI interfaces for any board that needs testing. 

1. If you want to test a SPI master device, then upload the SPI slave code to the arduino UNO 
and see if you can get any data onto the UNO to appear in your serial monitor (ref. UNO_Slave to see
what this means in detail)

OR. If you want to test a SPI slave device, then upload the SPI master code to the arduino UNO, and plug
in your slave device to test if it is properly recieving the SPI transmissions.

2. For UNO Master and Slave plug in cables as follows: 
SS:    Pin 10  (Slave Select)
MOSI:  Pin 11  (Master out slave in)
MISO:  Pin 12  (Master in slave out)
SCK:   Pin 13  (Serial Clock)


Some config examples (non-UNO boards only have example pins, only UNO pins are accurate):

Example 1: Testing an M4 master with an UNO Slave
Adafruit M4 (Master)      |         UNO (Slave)
SS:   Pin 4  --------------------  SS:   Pin 10
MOSI: Pin 12 --------------------  MOSI: Pin 11
MISO: Pin 13 --------------------  MISO: Pin 12
SCK:  Pin 15 --------------------  SCK:  Pin 13
(M4 pins not accurate)    |         (^UNO pins accurate)


Example 2: Testing a Teensy slave with an UNO master
UNO (Master)              |         Teensy (Slave)   
SS:   Pin 10 --------------------  SS:   Pin 3
MOSI: Pin 11 --------------------  MOSI: Pin 4
MISO: Pin 12 --------------------  MISO: Pin 6
SCK:  Pin 13 --------------------  SCK:  Pin 7
(UNO pins accurate)       |        (Teensy pins not accurate)


Example 3: Testing the UNO Master/Slave configuration with 2 Arduino Unos.
UNO (Master)              |         UNO (Slave)
SS:   Pin 10 --------------------  SS:   Pin 10
MOSI: Pin 11 --------------------  MOSI: Pin 11
MISO: Pin 12 --------------------  MISO: Pin 12
SCK:  Pin 13 --------------------  SCK:  Pin 13
(Use this configuration for UNO->UNO connection, all pins accurate)
