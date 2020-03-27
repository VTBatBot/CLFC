#define HWORDS 4096
uint16_t data[HWORDS];

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

void dma_init() {
  auto const splits = 8;

  // trigger on TCC OVF, update TCC duty, circular
  static DmacDescriptor descs[2 * splits] __attribute__((aligned(16)));
  static DmacDescriptor wrb __attribute__((aligned(16)));
  static uint32_t chnl0 = 0;  // DMA channel

  DMAC->BASEADDR.reg = (uint32_t)&descs[0];   //OK
  DMAC->WRBADDR.reg = (uint32_t)&wrb;            //OK
  DMAC->CTRL.bit.LVLEN0 =1 ;  // Activate all levels  /OK
  DMAC->CTRL.bit.LVLEN1 =1 ;                    //OK
  DMAC->CTRL.bit.LVLEN2 =1 ;                    //OK
  DMAC->CTRL.bit.LVLEN3 =1 ;                    //OK
  DMAC->CTRL.bit.DMAENABLE = 1;                 //OK  
  
  DMAC ->Channel[chnl0].CHCTRLA.bit.ENABLE = 0x0;
  DMAC ->Channel[chnl0].CHCTRLA.bit.SWRST = 0x1;
  DMAC->SWTRIGCTRL.reg &= (uint32_t)(~(1 << chnl0));
  DMAC ->Channel[chnl0].CHCTRLA.bit.BURSTLEN =0;  //Single beat burst     //OK
  DMAC ->Channel[chnl0].CHCTRLA.bit.TRIGACT = 0x0;   //Trigger per burst (beat)    //OK
  DMAC ->Channel[chnl0].CHCTRLA.bit.TRIGSRC = 0x16;   //TCCO OVF      //OK
  DMAC ->Channel[chnl0].CHPRILVL.bit.PRILVL = 0x0;   //Set channel priority level to 0.      //OK

  for (auto i = 0; i < 2 * splits; i++) {
    descs[i].DESCADDR.reg = (uint32_t) &descs[(i + 1) % (2 * splits)];
    descs[i].BTCTRL.bit.VALID    = 0x1; //Its a valid channel
    descs[i].BTCTRL.bit.BEATSIZE = 0x1;  // HWORD.
    descs[i].BTCTRL.bit.SRCINC   = 0x1;   //Source increment is enabled
    descs[i].BTCTRL.bit.DSTINC   = 0x0;   //Destination increment disabled
    descs[i].BTCNT.reg           = HWORDS/splits;   //Start with 20 transactions
    descs[i].SRCADDR.reg         = (uint32_t)&data + (i / 2 + 1) * (2 * (HWORDS / splits));   
    descs[i].DSTADDR.reg         = (uint32_t)&DAC->DATA[i % 2].reg;
  }

  /*
  descriptor.DESCADDR.reg = (uint32_t) &descriptor2;
  descriptor.BTCTRL.bit.VALID    = 0x1; //Its a valid channel
  descriptor.BTCTRL.bit.BEATSIZE = 0x1;  // HWORD.
  descriptor.BTCTRL.bit.SRCINC   = 0x1;   //Source increment is enabled
  descriptor.BTCTRL.bit.DSTINC   = 0x0;   //Destination increment disabled
  descriptor.BTCNT.reg           = HWORDS/2;   //Start with 20 transactions
  descriptor.SRCADDR.reg         = (uint32_t)&data + 2*HWORDS;   
  descriptor.DSTADDR.reg         = (uint32_t)&DAC->DATA[0].reg;

  descriptor2.DESCADDR.reg = (uint32_t) &descriptor3;
  descriptor2.BTCTRL.bit.VALID    = 0x1; //Its a valid channel
  descriptor2.BTCTRL.bit.BEATSIZE = 0x1;  // HWORD.
  descriptor2.BTCTRL.bit.SRCINC   = 0x1;   //Source increment is enabled
  descriptor2.BTCTRL.bit.DSTINC   = 0x0;   //Destination increment disabled
  descriptor2.BTCNT.reg           = HWORDS/2;   //Start with 20 transactions
  descriptor2.SRCADDR.reg         = (uint32_t)&data + HWORDS;   
  descriptor2.DSTADDR.reg         = (uint32_t)&DAC->DATA[1].reg;

  descriptor3.DESCADDR.reg = (uint32_t) &descriptor;
  descriptor3.BTCTRL.bit.VALID    = 0x1; //Its a valid channel
  descriptor3.BTCTRL.bit.BEATSIZE = 0x1;  // HWORD.
  descriptor3.BTCTRL.bit.SRCINC   = 0x1;   //Source increment is enabled
  descriptor3.BTCTRL.bit.DSTINC   = 0x0;   //Destination increment disabled
  descriptor3.BTCNT.reg           = HWORDS/2;   //Start with 20 transactions
  descriptor3.SRCADDR.reg         = (uint32_t)&data + HWORDS;   
  descriptor3.DSTADDR.reg         = (uint32_t)&DAC->DATA[1].reg;
  */
  
  // start channel
  DMAC ->Channel[chnl0].CHCTRLA.bit.ENABLE = 0x1;     //OK
  
  DMAC->CTRL.bit.DMAENABLE = 1;
}

void dac_init(){
    GCLK->GENCTRL[7].reg = GCLK_GENCTRL_DIV(1) |       // Divide the 48MHz clock source by divisor 1: 48MHz/1 = 48MHz
                             GCLK_GENCTRL_IDC |          // Set the duty cycle to 50/50 HIGH/LOW
                             GCLK_GENCTRL_GENEN |        // Enable GCLK7
                             //GCLK_GENCTRL_SRC_DFLL;      // Select 48MHz DFLL clock source
                             //GCLK_GENCTRL_SRC_DPLL1;     // Select 100MHz DPLL clock source
                             GCLK_GENCTRL_SRC_DPLL0;     // Select 120MHz DPLL clock source
    while (GCLK->SYNCBUSY.bit.GENCTRL7);               // Wait for synchronization  
    
    GCLK->PCHCTRL[42].reg = GCLK_PCHCTRL_CHEN |        // Enable the TCC0 peripheral channel
                              GCLK_PCHCTRL_GEN_GCLK7;    // Connect generic clock 7 to DAC
    MCLK->APBDMASK.bit.DAC_ = 1;
    
    DAC->CTRLA.bit.SWRST = 1;
    while(DAC->CTRLA.bit.SWRST);
    
    DAC->DACCTRL[0].reg = DAC_DACCTRL_REFRESH(2) |
          DAC_DACCTRL_CCTRL_CC12M |
          DAC_DACCTRL_ENABLE;// |
          DAC_DACCTRL_LEFTADJ;
          
    DAC->DACCTRL[1].reg = DAC_DACCTRL_REFRESH(2) |
          DAC_DACCTRL_CCTRL_CC12M |
          DAC_DACCTRL_ENABLE;// |
          DAC_DACCTRL_LEFTADJ;
          
    DAC->CTRLB.reg = DAC_CTRLB_REFSEL_VREFPB;
    DAC->DBGCTRL.bit.DBGRUN = 1;
    
    DAC->CTRLA.reg = DAC_CTRLA_ENABLE;
    while(DAC->SYNCBUSY.bit.ENABLE);
    while(!DAC->STATUS.bit.READY0);
    while(!DAC->STATUS.bit.READY1);
}

void setup() {
  for (auto i = 0; i < HWORDS; i++) data[i] = i;
  
  dac_init();
  dma_init();   // do me first
  timer_init();   // startup timer
 
}

void loop() {}
