#include <Adafruit_ZeroDMA.h>

#define DMAMEM __attribute__ ((section(".dmabuffers"), used))

DMAMEM static uint16_t dac_buffer[2 * 4096];
uint32_t *current_buffer;

Adafruit_ZeroDMA left, right;

void setup() {
  Serial.begin(1337);

  Serial.println("Whatup!");

  dac_init();

  for (auto i = 0; i < 2 * 4096; i++) dac_buffer[i] = i % 4096;
  
  {
    left.allocate();
  
    auto desc = left.addDescriptor(
      dac_buffer,
      (void *)(&DAC->DATA[0]),
      4096,
      DMA_BEAT_SIZE_HWORD,
      true,
      false);
    desc->BTCTRL.bit.BLOCKACT = DMA_BLOCK_ACTION_INT;
  
    left.setTrigger(0x16);
    left.setAction(DMA_TRIGGER_ACTON_BEAT);
  
    left.loop(true);
    left.setCallback(cb);
  
    left.startJob();
  }

  {
    right.allocate();
  
    auto desc = right.addDescriptor(
      &dac_buffer[4096],
      (void *)(&DAC->DATA[1]),
      4096,
      DMA_BEAT_SIZE_HWORD,
      true,
      false);
    desc->BTCTRL.bit.BLOCKACT = DMA_BLOCK_ACTION_INT;
  
    right.setTrigger(0x16);
    right.setAction(DMA_TRIGGER_ACTON_BEAT);
  
    right.loop(true);
    right.setCallback(cb);
  
    right.startJob();
  }

  timer_init();
}

void cb(Adafruit_ZeroDMA *dma) {
  
}

void timer_init() {
  GCLK->GENCTRL[7].reg = GCLK_GENCTRL_DIV(1) |       // Divide the 48MHz clock source by divisor 1: 48MHz/1 = 48MHz
                         GCLK_GENCTRL_IDC |          // Set the duty cycle to 50/50 HIGH/LOW
                         GCLK_GENCTRL_GENEN |        // Enable GCLK7
                         GCLK_GENCTRL_SRC_DFLL;      // Select 48MHz DFLL clock source
                         //GCLK_GENCTRL_SRC_DPLL1;     // Select 100MHz DPLL clock source
                        //GCLK_GENCTRL_SRC_DPLL0;     // Select 120MHz DPLL clock source
  while (GCLK->SYNCBUSY.bit.GENCTRL7);               // Wait for synchronization  

  GCLK->PCHCTRL[25].reg = GCLK_PCHCTRL_CHEN |        // Enable the TCC0 peripheral channel
                          GCLK_PCHCTRL_GEN_GCLK7;    // Connect generic clock 7 to TCC0

  // Enable the peripheral multiplexer on pin D7
  PORT->Group[g_APinDescription[7].ulPort].PINCFG[g_APinDescription[7].ulPin].bit.PMUXEN = 1;
  
  // Set the D7 (PORT_PB12) peripheral multiplexer to peripheral (even port number) E(6): TCC0, Channel 0
  PORT->Group[g_APinDescription[7].ulPort].PMUX[g_APinDescription[7].ulPin >> 1].reg |= PORT_PMUX_PMUXE(6);
  
  TCC0->CTRLA.reg = TC_CTRLA_PRESCALER_DIV4 |        // Set prescaler to 8, 48MHz/8 = 6MHz
                    TC_CTRLA_PRESCSYNC_PRESC;        // Set the reset/reload to trigger on prescaler clock                 

  TCC0->WAVE.reg = TC_WAVE_WAVEGEN_NPWM;             // Set-up TCC0 timer for Normal (single slope) PWM mode (NPWM)
  while (TCC0->SYNCBUSY.bit.WAVE)                    // Wait for synchronization

  TCC0->PER.reg = 12;                            // Set-up the PER (period) register 50Hz PWM
  while (TCC0->SYNCBUSY.bit.PER);                    // Wait for synchronization
  
  TCC0->CC[0].reg = 6;                           // Set-up the CC (counter compare), channel 0 register for 50% duty-cycle
  while (TCC0->SYNCBUSY.bit.CC0);                    // Wait for synchronization

  TCC0->CTRLA.bit.ENABLE = 1;                        // Enable timer TCC0
  while (TCC0->SYNCBUSY.bit.ENABLE);                 // Wait for synchronization
}


void dac_init() {
  while (DAC->SYNCBUSY.bit.ENABLE || DAC->SYNCBUSY.bit.SWRST);

  // Disable DAC
  DAC->CTRLA.bit.ENABLE = 0;
  while (DAC->SYNCBUSY.bit.ENABLE || DAC->SYNCBUSY.bit.SWRST);

  // Use an external reference voltage (see errata; the internal reference is busted)
  DAC->CTRLB.reg = DAC_CTRLB_REFSEL_VREFPB;
  while (DAC->SYNCBUSY.bit.ENABLE || DAC->SYNCBUSY.bit.SWRST);

  // Enable channels 0 and 1
  DAC->DACCTRL[0].bit.ENABLE = 1;
  DAC->DACCTRL[1].bit.ENABLE = 1;
  while (DAC->SYNCBUSY.bit.ENABLE || DAC->SYNCBUSY.bit.SWRST);

  // Enable DAC
  DAC->CTRLA.bit.ENABLE = 1;

  // Warm-up by sweeping from 0 to 3V3
  for (auto i = 0; i < 4096; i += 8) {
    while (!DAC->STATUS.bit.READY0 || !DAC->STATUS.bit.READY1);
    while (DAC->SYNCBUSY.bit.DATA0 || DAC->SYNCBUSY.bit.DATA1);
    
    DAC->DATA[0].reg = i;
    DAC->DATA[1].reg = i;
    
    delay(1);
  }
}

void loop() {
  Serial.println("Foobar!");

  delay(500);
}
