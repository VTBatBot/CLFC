/*
 *
 * Copyright (c) 2010 by Cristian Maglie <c.maglie@bug.st>
 * SPI Master library for arduino.
 *
 * This file is free software; you can redistribute it and/or modify
 * it under the terms of either the GNU General Public License version 2
 * or the GNU Lesser General Public License version 2.1, both as
 * published by the Free Software Foundation.
 */

#include "SPISlave.h"
#include "pins_arduino.h"

#define DEBUG_DMA_TRANSFERS


/**********************************************************/
/*     32 bit Teensy 4.x                                  */
/**********************************************************/


void _spi_dma_rxISR0(void) {SPI.dma_rxisr();}

const SPIClass::SPI_Hardware_t  SPIClass::spiclass_lpspi4_hardware = 
{
  CCM_CCGR1, CCM_CCGR1_LPSPI4(CCM_CCGR_ON),
  DMAMUX_SOURCE_LPSPI4_TX, 
  DMAMUX_SOURCE_LPSPI4_RX, 
  _spi_dma_rxISR0,
  12, 
  3 | 0x10,
  11,
  3 | 0x10,
  13,
  3 | 0x10,
  10,  // from https://forum.pjrc.com/threads/57328-Teensy-4-0-SPI-Chip-Select-pins If I remember correctly the one case, where you need to use the Hardware CS pin is if you implement an SPI Client setup, which I have not tried.

  3 | 0x10,
  IOMUXC_LPSPI4_SCK_SELECT_INPUT, 
  IOMUXC_LPSPI4_SDI_SELECT_INPUT, 
  IOMUXC_LPSPI4_SDO_SELECT_INPUT, 
  IOMUXC_LPSPI4_PCS0_SELECT_INPUT,
  0, 0, 0, 0
};

SPIClass SPI((uintptr_t)&IMXRT_LPSPI4_S, (uintptr_t)&SPIClass::spiclass_lpspi4_hardware);

// sketch defines these functions.
unsigned char *spiBuf();
void swapSpiBuf();


/*
LPSPI slave mode uses the same shift register and logic as the master mode, but does not
use the clock configuration register and the transmit command register must remain static
during SPI bus transfers.
*/


/*
  clock_gate_register = CCM_CCGR1  // 13.7.22 p 1140  
  clock_gate_mask = CCM_CCGR1_LPSPI4(CCM_CCGR_ON)   // CCM_CCGR_ON = 3
  tx_dma_channel = DMAMUX_SOURCE_LPSPI4_TX  // 80
  rx_dma_channel = DMAMUX_SOURCE_LPSPI4_RX  // 79
  dma_rxisr = SPI.gdr_isr
      
  cs_mux[0] = 3 | 0x10

  sck_select_input_register = IOMUXC_LPSPI4_SCK_SELECT_INPUT
  sdi_select_input_register = IOMUXC_LPSPI4_SDI_SELECT_INPUT
  sdo_select_input_register = IOMUXC_LPSPI4_SDO_SELECT_INPUT
  pcs0_select_input_register = IOMUXC_LPSPI4_PCS0_SELECT_INPUT
  
  sck_select_val = 0
  sdi_select_val = 0
  sdo_select_val = 0
  pcs0_select_val = 0
*/

static const int rxWater = 15;
//-----------------------------------------------------------------------------
void SPIClass::beginSlave()
//-----------------------------------------------------------------------------
{
//  Serial.printf( "clock_gate_register %08x\n", hardware().clock_gate_register );
//  Serial.printf( "clock_gate_mask %08x\n", hardware().clock_gate_mask );

    // turn off the LPSPI4 clock ( CCGR1 )
  // this is really CCM_CBCMR &= ~CCM_CCGR1_LPSPI4(CCM_CCGR_ON);
  hardware().clock_gate_register &= ~hardware().clock_gate_mask;


  Serial.printf( "SPI MISO: %d MOSI: %d, SCK: %d CS: %d\n", 
                   hardware().miso_pin[0], 
                   hardware().mosi_pin[0], 
                   hardware().sck_pin[0], 
                   hardware().cs_pin[0] );


    // CCM = Clock control module
  //Serial.printf( "before CBCMR = %08lX CCGR1 = %08lX\n", CCM_CBCMR, CCM_CCGR1 ); // CCM Bus Clock Multiplexer Register

    // IOMUXC = IOMUX Controller
  // SRE = slew rate fast
  // DSE(3) = Drive strength R0/5
  // SPEED(3) = max(200MHz) 

  uint32_t fastio = IOMUXC_PAD_DSE(6) | IOMUXC_PAD_SPEED(1);
  //uint32_t fastio = IOMUXC_PAD_SRE | IOMUXC_PAD_DSE(3) | IOMUXC_PAD_SPEED(3);

  *(portControlRegister(hardware().miso_pin[0])) = fastio;
  *(portControlRegister(hardware().mosi_pin[0])) = fastio;
  *(portControlRegister(hardware().sck_pin[0])) = fastio;


//  *(portControlRegister(16) = fastio;
//  *(portControlRegister(17) = fastio;
//  *(portControlRegister(19) = fastio;


    // turn on the LPSPI4 clock ( CCGR1 )
  // this is really CCM_CBCMR |= CCM_CCGR1_LPSPI4(CCM_CCGR_ON);
  hardware().clock_gate_register |= hardware().clock_gate_mask;

  Serial.printf( "after CBCMR = %08lX CCGR1 = %08lX\n", CCM_CBCMR, CCM_CCGR1 ); // CCM Bus Clock Multiplexer Register


  *(portConfigRegister(hardware().miso_pin[0])) 
     = hardware().miso_mux[0];
  *(portConfigRegister(hardware().mosi_pin[0])) 
     = hardware().mosi_mux[0];
  *(portConfigRegister(hardware().sck_pin[0])) 
     = hardware().sck_mux[0];

  // why do I need this in slave mode when master mode doesn't do it?
  *(portConfigRegister(hardware().cs_pin[0])) 
     = hardware().cs_mux[0];  


//  *(portConfigRegister(16) = IOMUXC_SW_MUX_CTL_PAD_GPIO_AD_B1_07;
//  *(portConfigRegister(17) = IOMUXC_SW_MUX_CTL_PAD_GPIO_AD_B1_06;
//  *(portConfigRegister(19) = IOMUXC_SW_MUX_CTL_PAD_GPIO_AD_B1_00;


  // Set the Mux pins 
    hardware().sck_select_input_register = hardware().sck_select_val;
  hardware().sdi_select_input_register = hardware().sdi_select_val;
  hardware().sdo_select_input_register = hardware().sdo_select_val;

    // why do I need this in slave mode when master mode doesn't do it?
  hardware().pcs0_select_input_register = hardware().pcs0_select_val;  
     
  // CR  = Control register
  // RST = Software reset
  port().CR = LPSPI_CR_RST;

  // Initialize the Receive FIFO watermark to FIFO size - 1... 
  port().FCR = LPSPI_FCR_RXWATER( rxWater );
  
  port().CR = LPSPI_CR_MEN;     // Module Enable

  
  initDMA();
  

  Serial.printf( "PARAM %x CR %x SR %x IER %x DER %x CFGR0 %x CFGR1 %x FCR %x TCR %x\n", 
                 port().PARAM,
                 port().CR, port().SR, 
           port().IER, port().DER,
           port().CFGR0, port().CFGR1, 
           port().FCR, port().TCR );  
}


static int const BufSize = 3000;


//-----------------------------------------------------------------------------
bool SPIClass::initDMAChannels() 
//-----------------------------------------------------------------------------
{
  _dmaRX = new DMAChannel();

  if (_dmaRX == nullptr)
    return false;

Serial.printf( "rx_dma_channel = %d\n", hardware().rx_dma_channel );

  // Set up the RX chain
  _dmaRX->disable();

  _dmaRX->source( (volatile uint8_t&)port().RDR );
/*
Disable Request
If this flag is set, the eDMA hardware automatically clears the corresponding ERQ bit when the current
major iteration count reaches zero.
0b - The channel's ERQ bit is not affected.
1b - The channel's ERQ bit is cleared when the major loop is complete.
*/
  _dmaRX->disableOnCompletion();   // TCD->CSR |= DMA_TCD_CSR_DREQ;
  _dmaRX->triggerAtHardwareEvent( hardware().rx_dma_channel );
  _dmaRX->attachInterrupt( hardware().dma_rxisr );

/*
Enable an interrupt when major iteration count completes.
If this flag is set, the channel generates an interrupt request by setting the appropriate bit in the INT when
the current major iteration count reaches zero.
0b - The end-of-major loop interrupt is disabled.
1b - The end-of-major loop interrupt is enabled.
*/

    // cause the dma_rxisr() to be called at the end of the transfer
  _dmaRX->interruptAtCompletion();  // TCD->CSR |= DMA_TCD_CSR_INTMAJOR;
  
  _dma_state = DMAState::idle;  // Should be first thing set!
  
  _dmaRX->enable(); 
  
  return true;
}


EventResponder _event_responder;

#define DATA_BUFFER_MAX (16*1024)

//-----------------------------------------------------------------------------
bool SPIClass::initDMA()
//-----------------------------------------------------------------------------
{ 
  initDMAChannels();
  
  
    if (_dma_state == DMAState::active)
    return false; // already active

  _event_responder.clearEvent();  // Make sure it is not set yet
  
  _dma_count_remaining = 0;
  
  _dmaRX->TCD->ATTR_SRC = 0;    // Make sure set for 8 bit mode...
  _dmaRX->destinationBuffer((uint8_t*)spiBuf(), BufSize );
  _dmaRX->TCD->DLASTSGA = -BufSize;

  if( (uint32_t)spiBuf() >= 0x20200000u )  
    arm_dcache_delete( spiBuf(), BufSize );
  
  _dma_event_responder = &_event_responder;

  dumpDMA_TCD( _dmaRX );

  // Make sure port is in 8 bit mode and clear watermark
  port().TCR = (port().TCR & ~(LPSPI_TCR_FRAMESZ(31))) | LPSPI_TCR_FRAMESZ(7);  
  port().FCR = 0; 

  // Lets try to output the first byte to make sure that we are in 8 bit mode...
  port().DER = LPSPI_DER_RDDE;  //enable DMA on RX
  port().SR = 0x3f00; // clear out all of the other status...

  _dmaRX->enable();

  _dma_state = DMAState::active;
  
  return true;
}



//-----------------------------------------------------------------------------
inline void DMAChanneltransferCount( DMAChannel *dmac, unsigned int len ) 
//-----------------------------------------------------------------------------
{
  // note does no validation of length...
  DMABaseClass::TCD_t *tcd = dmac->TCD;
  
  if (!(tcd->BITER & DMA_TCD_BITER_ELINK)) 
  {
    tcd->BITER = len & 0x7fff;
  } 
  else 
  {
    tcd->BITER = (tcd->BITER & 0xFE00) | (len & 0x1ff);
  }
  tcd->CITER = tcd->BITER; 
}

//-----------------------------------------------------------------------------
void dumpDMA_TCD( DMABaseClass *dmabc )
//-----------------------------------------------------------------------------
{
  Serial.printf("spiData = %p BC: %x TCD: %x:", spiBuf(), (uint32_t)dmabc, (uint32_t)dmabc->TCD);

  Serial.printf("SA:%x SO:%d AT:%x NB:%x SL:%d DA:%x DO:%d CI:%x DL:%x CS:%x BI:%x\n", (uint32_t)dmabc->TCD->SADDR,
    dmabc->TCD->SOFF, dmabc->TCD->ATTR, dmabc->TCD->NBYTES, dmabc->TCD->SLAST, (uint32_t)dmabc->TCD->DADDR, 
    dmabc->TCD->DOFF, dmabc->TCD->CITER, dmabc->TCD->DLASTSGA, dmabc->TCD->CSR, dmabc->TCD->BITER);
}


//-------------------------------------------------------------------------
void SPIClass::dma_rxisr() 
//-------------------------------------------------------------------------
{
  _dmaRX->clearInterrupt();   //    DMA_CINT = channel;
  _dmaRX->clearComplete();    //    DMA_CDNE = channel;
  
  // receive a full SPI buffer
    DMAChanneltransferCount( _dmaRX, BufSize );

    // Optionally allow the user to double buffer the data.  Comment 
  //   the swapSpiBuf() functions out if you don't need them.
    ::swapSpiBuf();   // swap the pointers
    swapSpiBuf();     // tell _dmaRX the new buffer
  
  
    _dmaRX->enable();

    asm("dsb");

}

  
//-------------------------------------------------------------------------
void swapSpiBuf()
//-------------------------------------------------------------------------
{ 
  _dmaRX->destinationBuffer((uint8_t*)spiBuf(), BufSize ); 
}
