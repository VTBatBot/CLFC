#define VERSION_MAJOR 0
#define VERSION_MINOR 2

// 1.6 MHz is the max frequency of the DAC, so it's easiest
// just to scale everything off of it. 1 ADC channel runs at
// 41.25% (~660 kHz); 2 ADC channels run at 25% (400 kHz each)
const int freq = 3000;

// The ADC channels to sample. Note that the port numbers on the
// Due (A0-7) count in reverse order to the SAM3X's channels (CH7-0),
// i.e. A0 is CH7 and A1 is CH6
const int adc_channels = ADC_CHER_CH7;
// Number of channels listed above
const int num_adc_channels = 1;
// Size of each block in the ADC buffer
const int adc_block_size = 200 * num_adc_channels;
// Number of samples to collect in total, for all channels
const int num_adc_samples = 45000;
// Number of blocks in the ADC buffer
const int num_adc_blocks = num_adc_samples / adc_block_size;

// Internal index of the current block within the DAC buffer
volatile uint16_t adc_block_index = 0;
// Buffers to store data that is converted from the ADC. Sampling for
// a longer time requires either flushing these buffers out perioidcally,
// or just increasing their size. Currently this does the latter which is
// not very scalable and should be resolved later on
volatile uint16_t input_waveforms[num_adc_blocks][adc_block_size];

// Flag to indicate that the data collection is finished and the buffers
// can be dumped
volatile bool data_ready = false;

void setup() {
  // USB serial is performed at native speed, negotiated by the host.
  // The baud rate set here will be ignored
  SerialUSB.begin(1337);

  // Enable output on B ports
  REG_PIOB_OWER = 0xFFFFFFFF;
  REG_PIOB_OER =  0xFFFFFFFF;
}

void loop() {
  static bool collect_data = false;
  
  // Don't poll while we're collecting data (although this is unlikely to be
  // hit considering all of the cycles are consumed by the timer)
  if (collect_data && !data_ready) {
    return;
  }

  // Transmit the collected data when it's ready
  if (data_ready) {
    int body_len = num_adc_blocks*adc_block_size*2;
    char header[5] = { 
      0x82,
      (body_len >> 0*8) & 0xff,
      (body_len >> 1*8) & 0xff,
      (body_len >> 2*8) & 0xff,
      (body_len >> 3*8) & 0xff,
    };
    SerialUSB.write(header, 5);
  
    for (int n = 0; n < num_adc_blocks; n++) {
        SerialUSB.write((uint8_t *)input_waveforms[n], adc_block_size);
        SerialUSB.write((uint8_t *)input_waveforms[n] + adc_block_size, adc_block_size);
    }
    
    data_ready = false;
    collect_data = false;
  }

  // Poll for incoming request packets
  // A packet header consists of an opcode (1 byte) and body length (4 bytes)
  if (SerialUSB.available() >= 5) {
    uint8_t opcode = SerialUSB.read();
    // We enforce little-endian for all communications.
    // Do not combine these lines: the lack of a sequence point
    // would cause undefined behavior as the calls to read() have
    // side effects
    uint32_t input_len = SerialUSB.read();
    input_len = input_len | (SerialUSB.read() << 8);
    input_len = input_len | (SerialUSB.read() << 16);
    input_len = input_len | (SerialUSB.read() << 24);

    // Dispatch the packet to its handler
    switch (opcode) {
      // Hello
      case 0x00: {
        char response[7] = {
          opcode | 0x80,
          2, 0, 0, 0,
          VERSION_MAJOR, VERSION_MINOR
        };
        SerialUSB.write(response, 7);
        break;
      }

      // Collect data (static)
      case 0x02: {
        char response[5] = { opcode | 0x80, 0, 0, 0, 0 };
        SerialUSB.write(response, 5);
        
        collect_data = true;
        
        reset();
        break;
      }

      // Unknown
      default: {
        char response[255] = {0};
        response[0] = 0xff;
        int msg_len = snprintf(&response[5], 250, "Unknown opcode %i", opcode);
        response[1] = (uint8_t)(msg_len);
        response[2] = (uint8_t)(msg_len >> 8);
        response[3] = (uint8_t)(msg_len >> 16);
        response[4] = (uint8_t)(msg_len >> 24);
        SerialUSB.write(response, msg_len + 5);
        break;
      }
    }
  }
}


/*****************************************************************************
 * HERE BE DRAGONS:
 *
 * Everything below this is micro-controller specific and probably not
 * something worth looking at or modifying
 *****************************************************************************/


// Initialize the timer peripheral TC0
void setup_timer() {
  // Enable the clock of the peripheral
  pmc_enable_periph_clk(TC_INTERFACE_ID);

  TC_Configure(TC0, 0,
    // Waveform mode
    TC_CMR_WAVE |
    // Count-up with RC as the threshold
    TC_CMR_WAVSEL_UP_RC |
    // Clear on RA and set on RC
    TC_CMR_ACPA_CLEAR | TC_CMR_ACPC_SET |
    TC_CMR_ASWTRG_CLEAR |
    // Prescale by 2 (MCK/2=42MHz)
    TC_CMR_TCCLKS_TIMER_CLOCK1);

  uint32_t rc = SystemCoreClock / (2 * freq);
  // Achieve a duty cycle of 50% by clearing after half a period
  TC_SetRA(TC0, 0, rc / 2);
  // Set the period
  TC_SetRC(TC0, 0, rc);
  TC_Start(TC0, 0);

  // Enable the interrupts with the controller
  NVIC_EnableIRQ(TC0_IRQn);
}

// Initialize the ADC peripheral
void setup_adc() {
  // Reset the controller
  ADC->ADC_CR = ADC_CR_SWRST;
  // Reset all of the configuration options
  ADC->ADC_MR = 0;
  // Stop any transfers
  ADC->ADC_PTCR = (ADC_PTCR_RXTDIS | ADC_PTCR_TXTDIS);

  // Setup timings
  ADC->ADC_MR |= ADC_MR_PRESCAL(1);
  ADC->ADC_MR |= ADC_MR_STARTUP_SUT24;
  ADC->ADC_MR |= ADC_MR_TRACKTIM(1);
  ADC->ADC_MR |= ADC_MR_SETTLING_AST3;
  ADC->ADC_MR |= ADC_MR_TRANSFER(1);
  // Use a hardware trigger
  ADC->ADC_MR |= ADC_MR_TRGEN_EN;
  // Trigger on timer 0, channel 0 (TC0)
  ADC->ADC_MR |= ADC_MR_TRGSEL_ADC_TRIG1;
  // Enable the necessary channels
  ADC->ADC_CHER = adc_channels;

  // Load the DMA buffer
  ADC->ADC_RPR  = (uint32_t)input_waveforms[0];
  ADC->ADC_RCR  = adc_block_size;
  if (num_adc_blocks > 1) {
    ADC->ADC_RNPR = (uint32_t)input_waveforms[1];
    ADC->ADC_RNCR = adc_block_size;
    adc_block_index++;
  }

  // Enable an interrupt when the end of the DMA buffer is reached
  ADC->ADC_IDR = ~ADC_IDR_ENDRX;
  ADC->ADC_IER = ADC_IER_ENDRX;
  NVIC_EnableIRQ(ADC_IRQn);
  
  // Enable receiving data
  ADC->ADC_PTCR = ADC_PTCR_RXTEN;
  // Wait for a trigger
  ADC->ADC_CR |= ADC_CR_START;
}

// A junk variable we point the DMA buffer to before stopping the ADC.
// This is to ensure that we don't overwrite anything, but might not
// be entirely necessary
uint16_t adc_junk_space[1] = {0};

// Interrupt handler for the ADC peripheral
void ADC_Handler() {
  if (ADC->ADC_ISR & ADC_ISR_ENDRX)  {
    if (adc_block_index >= num_adc_blocks) {
      adc_stop(ADC);
      TC_Stop(TC0, 0);
      
      data_ready = true;
      
      ADC->ADC_RPR = ADC->ADC_RNPR = (uint32_t)adc_junk_space;
      ADC->ADC_RCR = ADC->ADC_RNCR = 1;
      return;
    }
    ADC->ADC_RNPR  = (uint32_t)input_waveforms[++adc_block_index % num_adc_blocks];
    ADC->ADC_RNCR  = adc_block_size;
  }
}

// Reset all of the peripherals
void reset() {
  adc_block_index = 0;

  // Temporarily disable write-protection for the power controller
  // while we enable peripheral clocks
  pmc_set_writeprotect(false);
  setup_adc();
  setup_timer();
  pmc_set_writeprotect(true);
}
