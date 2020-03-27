#include <Adafruit_ZeroDMA.h>
#include <wiring_private.h>  // for access to pinPeripheral

// Duration of waveforms in ms
constexpr int DURATION = 30;

constexpr int PAGE_SIZE = 4096;
// It takes ~4.4ms to collect 4096 readings, so round up to the nearest multiple
constexpr int NUM_PAGES = (DURATION + 4.4) / 4.4;

// Create buffers for DMAing data around -- the .dmabuffers section is supposed to
// optimize the memory location for the DMA controller
__attribute__ ((section(".dmabuffers"), used))
uint16_t left_in_buffers[NUM_PAGES][PAGE_SIZE], right_in_buffers[NUM_PAGES][PAGE_SIZE], out_buffers[NUM_PAGES][PAGE_SIZE];

// Index of the page currently being accessed
uint16_t left_in_index, right_in_index, out_index;

// 
DmacDescriptor *left_in_descs[NUM_PAGES], *right_in_descs[NUM_PAGES], *out_descs[NUM_PAGES];

Adafruit_ZeroDMA left_in_dma, right_in_dma, out_dma;

void setup() {
  // Serial doesn't work for the first second or two???
  delay(2000);

  // Initialize all of the buffers
  for (auto i = 0; i < NUM_PAGES; i++)
    for (auto j = 0; j < PAGE_SIZE; j++) {
      left_in_buffers[i][j] = 0;
      right_in_buffers[i][j] = 0;
      out_buffers[i][j] = i * 500;
    }
  left_in_index = right_in_index = out_index = 0;

  clock_init();

  // Initialize peripherals
  adc_init(A1, ADC0);
  adc_init(A3, ADC1);
  dac_init();
  dma_init();
  timer_init();

  // Trigger both ADCs to enter free-run mode
  ADC0->SWTRIG.bit.START = 1;
  ADC1->SWTRIG.bit.START = 1;
}

bool data_ready = false;

void loop() {
  if (Serial.available()) {
    uint8_t opcode = Serial.read();

    // Start run
    if (opcode == 0x10) {
      data_ready = false;
      left_in_index = right_in_index = out_index = 0;

      // Start all DMA jobs
      DMAC->CTRL.bit.DMAENABLE = 0;
      left_in_dma.startJob();
      right_in_dma.startJob();
      out_dma.startJob();
      DMAC->CTRL.bit.DMAENABLE = 1;
    }
    // Check run status
    else if (opcode == 0x20) {
      Serial.write(data_ready);
    }
    // Retreive left buffer
    else if (opcode == 0x30) {
      Serial.write(NUM_PAGES - left_in_index);
      while (left_in_index < NUM_PAGES) {
        Serial.write(reinterpret_cast<uint8_t *>(left_in_buffers[left_in_index++]), sizeof(uint16_t) * PAGE_SIZE);
      }
    }
    // Retreive right buffer
    else if (opcode == 0x31) {
      Serial.write(NUM_PAGES - right_in_index);
      while (right_in_index < NUM_PAGES) {
        Serial.write(reinterpret_cast<uint8_t *>(right_in_buffers[right_in_index++]), sizeof(uint16_t) * PAGE_SIZE);
      }
    }
  }

  // Check if the run is complete yet
  if (!data_ready && left_in_index == NUM_PAGES && right_in_index == NUM_PAGES && out_index == NUM_PAGES) {
    data_ready = true;

    left_in_index = right_in_index = out_index = 0;
  }
}

void dma_left_complete(Adafruit_ZeroDMA *dma) {
  left_in_index++;
}

void dma_right_complete(Adafruit_ZeroDMA *dma) {
  right_in_index++;
}

void dma_out_complete(Adafruit_ZeroDMA *dma) {
  out_index++;

  digitalWrite(5, HIGH);
  digitalWrite(5, LOW);
}

void spi_init() {
  // Reset
  SERCOM7->SPI.CTRLA.bit.SWRST = 1;
  while (SERCOM7->SPI.CTRLA.bit.SWRST || SERCOM7->SPI.SYNCBUSY.bit.SWRST);

  //TODO fix clock NVIC

  // Initialize the peripheral
  SERCOM7->SPI.CTRLA.reg = SERCOM_SPI_CTRLA_MODE(0x3)  | // master mode
                           SERCOM_SPI_CTRLA_DOPO(0) | // pad 0 sck 1
                           SERCOM_SPI_CTRLA_DIPO(0) | // pad 0
                           (0 << SERCOM_SPI_CTRLA_DORD_Pos); // MSB first
  SERCOM7->SPI.CTRLB.reg = SERCOM_SPI_CTRLB_CHSIZE(0) | // 8-bit characters
                          SERCOM_SPI_CTRLB_RXEN; // enable receiving
  while (SERCOM7->SPI.SYNCBUSY.bit.CTRLB);

  //TODO initialize the clock properly

  // Enable the peripheral
  SERCOM7->SPI.CTRLA.bit.ENABLE = 1;
  while (SERCOM7->SPI.SYNCBUSY.bit.ENABLE);
  
  static Adafruit_ZeroDMA spi_out_dma;

  // Create a DMA descriptor for feeding data into 
  spi_out_dma.allocate();
}

void clock_init() {
  // Create a new generic 48MHz clock for our timer
  GCLK->GENCTRL[7].reg = GCLK_GENCTRL_DIV(1) |       // Divide the 48MHz clock source by divisor 1: 48MHz/1 = 48MHz
                         GCLK_GENCTRL_IDC |          // Set the duty cycle to 50/50 HIGH/LOW
                         GCLK_GENCTRL_GENEN |        // Enable GCLK7
                         GCLK_GENCTRL_SRC_DFLL;      // Select 48MHz DFLL clock source
  while (GCLK->SYNCBUSY.bit.GENCTRL7);

  // Setup TCC0's clock
  GCLK->PCHCTRL[TCC0_GCLK_ID].reg = GCLK_PCHCTRL_CHEN | GCLK_PCHCTRL_GEN_GCLK7;
  
  // Setup ADC1's clock (ADC0 is pre-configured by Arduino)
  // (Not true?)
  GCLK->PCHCTRL[ADC1_GCLK_ID].reg = GCLK_PCHCTRL_GEN_GCLK1_Val | (1 << GCLK_PCHCTRL_CHEN_Pos);
}

void timer_init() {
  TCC0->CTRLA.reg = TC_CTRLA_PRESCALER_DIV4 |        // Set prescaler to 8, 48MHz/8 = 6MHz
                    TC_CTRLA_PRESCSYNC_PRESC;        // Set the reset/reload to trigger on prescaler clock                 

  TCC0->WAVE.reg = TC_WAVE_WAVEGEN_NPWM;             // Set-up TCC0 timer for Normal (single slope) PWM mode (NPWM)
  while (TCC0->SYNCBUSY.bit.WAVE);

  TCC0->PER.reg = 12;                            // Set-up the PER (period) register 50Hz PWM
  while (TCC0->SYNCBUSY.bit.PER);
  
  TCC0->CC[0].reg = 6;                           // Set-up the CC (counter compare), channel 0 register for 50% duty-cycle
  while (TCC0->SYNCBUSY.bit.CC0);

  TCC0->CTRLA.bit.ENABLE = 1;                        // Enable timer TCC0
  while (TCC0->SYNCBUSY.bit.ENABLE);
}

void dma_init() {
  {
    left_in_dma.allocate();
  
    for (auto i = 0; i < NUM_PAGES; i++) {
      left_in_descs[i] = left_in_dma.addDescriptor(
        (void *)(&ADC0->RESULT.reg),
        left_in_buffers[i],
        PAGE_SIZE,
        DMA_BEAT_SIZE_HWORD,
        false,
        true);
      left_in_descs[i]->BTCTRL.bit.BLOCKACT = DMA_BLOCK_ACTION_INT;
    }

    //left_in_dma.loop(true);
    left_in_dma.setTrigger(0x44);
    left_in_dma.setAction(DMA_TRIGGER_ACTON_BEAT);
    left_in_dma.setCallback(dma_left_complete);
  }

  {
    right_in_dma.allocate();
  
    for (auto i = 0; i < NUM_PAGES; i++) {
      right_in_descs[i] = right_in_dma.addDescriptor(
        (void *)(&ADC1->RESULT.reg),
        right_in_buffers[i],
        PAGE_SIZE,
        DMA_BEAT_SIZE_HWORD,
        false,
        true);
      right_in_descs[i]->BTCTRL.bit.BLOCKACT = DMA_BLOCK_ACTION_INT;
    }

    //right_in_dma.loop(true);
    right_in_dma.setTrigger(0x46);
    right_in_dma.setAction(DMA_TRIGGER_ACTON_BEAT);
    right_in_dma.setCallback(dma_right_complete);
  }

  {
    out_dma.allocate();
  
    for (auto i = 0; i < NUM_PAGES; i++) {
      out_descs[i] = out_dma.addDescriptor(
        out_buffers[i],                                                                                                                                     
        (void *)(&DAC->DATA[0]),
        PAGE_SIZE,
        DMA_BEAT_SIZE_HWORD,
        true,
        false);
      out_descs[i]->BTCTRL.bit.BLOCKACT = DMA_BLOCK_ACTION_INT;
    }

    //out_dma.loop(true);
    out_dma.setTrigger(0x16);
    out_dma.setAction(DMA_TRIGGER_ACTON_BEAT);
    out_dma.setCallback(dma_out_complete);
  }
}

void dac_init() {
  // Disable DAC
  DAC->CTRLA.bit.ENABLE = 0;
  while (DAC->SYNCBUSY.bit.ENABLE || DAC->SYNCBUSY.bit.SWRST);

  // Use an external reference voltage (see errata; the internal reference is busted)
  DAC->CTRLB.reg = DAC_CTRLB_REFSEL_VREFPB;
  while (DAC->SYNCBUSY.bit.ENABLE || DAC->SYNCBUSY.bit.SWRST);

  // Enable channel 0
  DAC->DACCTRL[0].bit.ENABLE = 1;
  while (DAC->SYNCBUSY.bit.ENABLE || DAC->SYNCBUSY.bit.SWRST);

  // Enable DAC
  DAC->CTRLA.bit.ENABLE = 1;
  while (DAC->SYNCBUSY.bit.ENABLE || DAC->SYNCBUSY.bit.SWRST);
}

void adc_init(int inpselCFG, Adc *ADCx) {
  // Configure the ADC pin (cheating method)
  pinPeripheral(inpselCFG, PIO_ANALOG);
  
  ADCx->INPUTCTRL.reg = ADC_INPUTCTRL_MUXNEG_GND;   // No Negative input (Internal Ground)
  while( ADCx->SYNCBUSY.reg & ADC_SYNCBUSY_INPUTCTRL );
  
  ADCx->INPUTCTRL.bit.MUXPOS = g_APinDescription[inpselCFG].ulADCChannelNumber; // Selection for the positive ADC input
  while( ADCx->SYNCBUSY.reg & ADC_SYNCBUSY_INPUTCTRL );
  
  ADCx->CTRLA.bit.PRESCALER = ADC_CTRLA_PRESCALER_DIV4_Val;
  while( ADCx->SYNCBUSY.reg & ADC_SYNCBUSY_CTRLB );
  
  ADCx->CTRLB.bit.RESSEL = ADC_CTRLB_RESSEL_12BIT_Val;
  while( ADCx->SYNCBUSY.reg & ADC_SYNCBUSY_CTRLB );
  
  ADCx->SAMPCTRL.reg = 0x0;                        
  while( ADCx->SYNCBUSY.reg & ADC_SYNCBUSY_SAMPCTRL );
  
  ADCx->AVGCTRL.reg = ADC_AVGCTRL_SAMPLENUM_1 |    // 1 sample only (no oversampling nor averaging)
            ADC_AVGCTRL_ADJRES(0x0ul);   // Adjusting result by 0
  while( ADCx->SYNCBUSY.reg & ADC_SYNCBUSY_AVGCTRL );
  
  ADCx->REFCTRL.bit.REFSEL = ADC_REFCTRL_REFSEL_AREFA_Val; // 1/2 VDDANA = 0.5* 3V3 = 1.65V
  while(ADCx->SYNCBUSY.reg & ADC_SYNCBUSY_REFCTRL);
  
  ADCx->CTRLB.reg |= 0x02;  ; //FREERUN
  while( ADCx->SYNCBUSY.reg & ADC_SYNCBUSY_CTRLB);
  
  ADCx->CTRLA.bit.ENABLE = 0x01;
  while( ADCx->SYNCBUSY.reg & ADC_SYNCBUSY_ENABLE );
}
