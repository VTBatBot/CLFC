/*
 * Copyright (c) 2010 by Cristian Maglie <c.maglie@bug.st>
 * Copyright (c) 2014 by Paul Stoffregen <paul@pjrc.com> (Transaction API)
 * Copyright (c) 2014 by Matthijs Kooijman <matthijs@stdin.nl> (SPISettings AVR)
 * SPI Master library for arduino.
 *
 * This file is free software; you can redistribute it and/or modify
 * it under the terms of either the GNU General Public License version 2
 * or the GNU Lesser General Public License version 2.1, both as
 * published by the Free Software Foundation.
 */

#ifndef _SPI_SLAVE_H_INCLUDED
#define _SPI_SLAVE_H_INCLUDED

#include <Arduino.h>

#if defined(__arm__) && defined(TEENSYDUINO)
#if defined(__has_include) && __has_include(<EventResponder.h>)
// SPI_HAS_TRANSFER_ASYNC - Defined to say that the SPI supports an ASYNC version
// of the SPI_HAS_TRANSFER_BUF
#define SPI_HAS_TRANSFER_ASYNC 1
#include <DMAChannel.h>
#include <EventResponder.h>
#endif
#endif

// SPI_HAS_TRANSACTION means SPI has beginTransaction(), endTransaction(),
// usingInterrupt(), and SPISetting(clock, bitOrder, dataMode)
#define SPI_HAS_TRANSACTION 1

// Uncomment this line to add detection of mismatched begin/end transactions.
// A mismatch occurs if other libraries fail to use SPI.endTransaction() for
// each SPI.beginTransaction().  Connect a LED to this pin.  The LED will turn
// on if any mismatch is ever detected.
//#define SPI_TRANSACTION_MISMATCH_LED 5

// SPI_HAS_TRANSFER_BUF - is defined to signify that this library supports
// a version of transfer which allows you to pass in both TX and RX buffer
// pointers, either of which could be NULL
#define SPI_HAS_TRANSFER_BUF 1


#ifndef LSBFIRST
#define LSBFIRST 0
#endif
#ifndef MSBFIRST
#define MSBFIRST 1
#endif

#define SPI_MODE0 0x00
#define SPI_MODE1 0x04
#define SPI_MODE2 0x08
#define SPI_MODE3 0x0C

#define SPI_CLOCK_DIV4 0x00
#define SPI_CLOCK_DIV16 0x01
#define SPI_CLOCK_DIV64 0x02
#define SPI_CLOCK_DIV128 0x03
#define SPI_CLOCK_DIV2 0x04
#define SPI_CLOCK_DIV8 0x05
#define SPI_CLOCK_DIV32 0x06

#define SPI_MODE_MASK 0x0C  // CPOL = bit 3, CPHA = bit 2 on SPCR
#define SPI_CLOCK_MASK 0x03  // SPR1 = bit 1, SPR0 = bit 0 on SPCR
#define SPI_2XCLOCK_MASK 0x01  // SPI2X = bit 0 on SPSR



/**********************************************************/
/*     32 bit Teensy 4.x                                  */
/**********************************************************/

#if defined(__arm__) && defined(TEENSYDUINO) && (defined(__IMXRT1052__) || defined(__IMXRT1062__))
#define SPI_ATOMIC_VERSION 1

void synchronousRead_isr(void);


class DMABaseClass;


void dumpDMA_TCD( DMABaseClass *dmabc );


class SPISettings 
{
public:
  SPISettings(uint32_t clockIn, uint8_t bitOrderIn, uint8_t dataModeIn) : _clock
  (clockIn) 
  {
    init_AlwaysInline(bitOrderIn, dataModeIn);
  }

  SPISettings() : _clock(4000000) 
  {
    init_AlwaysInline(MSBFIRST, SPI_MODE0);
  }
private:
  void init_AlwaysInline(uint8_t bitOrder, uint8_t dataMode)
    __attribute__((__always_inline__)) 
    {
      tcr = LPSPI_TCR_FRAMESZ(7);    // TCR has polarity and bit order too

      // handle LSB setup 
      if (bitOrder == LSBFIRST) tcr |= LPSPI_TCR_LSBF;

      // Handle Data Mode
      if (dataMode & 0x08) tcr |= LPSPI_TCR_CPOL;

      // Note: On T3.2 when we set CPHA it also updated the timing.  It moved the 
      // PCS to SCK Delay Prescaler into the After SCK Delay Prescaler  
      if (dataMode & 0x04) tcr |= LPSPI_TCR_CPHA; 
  }

  inline uint32_t clock() {return _clock;}

  uint32_t _clock;
  uint32_t tcr; // transmit command, pg 2955
  friend class SPIClass;
};



class SPIClass // Teensy 4
{ 
public:
  static const uint8_t CNT_MISO_PINS = 1;
  static const uint8_t CNT_MOSI_PINS = 1;
  static const uint8_t CNT_SCK_PINS = 1;
  static const uint8_t CNT_CS_PINS = 1;
  
  struct SPI_Hardware_t
  {
    volatile uint32_t &clock_gate_register;
    const uint32_t clock_gate_mask;
    uint8_t  tx_dma_channel;
    uint8_t  rx_dma_channel;
    void     (*dma_rxisr)();
    const uint8_t  miso_pin[CNT_MISO_PINS];
    const uint32_t  miso_mux[CNT_MISO_PINS];
    const uint8_t  mosi_pin[CNT_MOSI_PINS];
    const uint32_t  mosi_mux[CNT_MOSI_PINS];
    const uint8_t  sck_pin[CNT_SCK_PINS];
    const uint32_t  sck_mux[CNT_SCK_PINS];
    const uint8_t  cs_pin[CNT_CS_PINS];
    const uint32_t  cs_mux[CNT_CS_PINS];

    volatile uint32_t &sck_select_input_register;
    volatile uint32_t &sdi_select_input_register;
    volatile uint32_t &sdo_select_input_register;
    volatile uint32_t &pcs0_select_input_register;
    const uint8_t sck_select_val;
    const uint8_t sdi_select_val;
    const uint8_t sdo_select_val;
    const uint8_t pcs0_select_val;
  };
  
  static const SPI_Hardware_t spiclass_lpspi4_hardware;
  static const SPI_Hardware_t spiclass_lpspi3_hardware;
  static const SPI_Hardware_t spiclass_lpspi1_hardware;


public:
  constexpr SPIClass(uintptr_t myport, uintptr_t myhardware)
    : port_addr(myport), hardware_addr(myhardware) 
  {
  }

  void beginSlave();

  bool initDMA();
  
  void swapSpiBuf()
  { 
     _dmaRX->destinationBuffer((uint8_t*)spiBuf(), BufSize ); 
  }
  

  friend void _spi_dma_rxISR0();
  inline void dma_rxisr();


public:
  IMXRT_LPSPI_t & port() { return *(IMXRT_LPSPI_t *)port_addr; }

private:
  const SPI_Hardware_t & hardware() { return *(const SPI_Hardware_t *)hardware_addr; }
  uintptr_t port_addr;
  uintptr_t hardware_addr;

  uint32_t _clock = 0;
  uint32_t _ccr = 0;

  uint8_t miso_pin_index = 0;
  uint8_t mosi_pin_index = 0;
  uint8_t sck_pin_index = 0;
  
  uint8_t interruptMasksUsed = 0;
  uint32_t interruptMask[(NVIC_NUM_INTERRUPTS+31)/32] = {};
  uint32_t interruptSave[(NVIC_NUM_INTERRUPTS+31)/32] = {};
  

  // DMA Support
  bool initDMAChannels();
  enum DMAState { notAllocated, idle, active, completed};
  enum { MAX_DMA_COUNT = 32767 };
  DMAState _dma_state = DMAState::notAllocated;
  uint32_t _dma_count_remaining = 0;  // How many bytes left to output after current DMA completes
  
  DMAChannel *_dmaRX = nullptr;
  EventResponder *_dma_event_responder = nullptr;

};


#endif


extern SPIClass SPI;
extern SPIClass SPI1;
extern SPIClass SPI2;

#endif
