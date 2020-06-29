#include <atmel_start.h>
#include <hal_timer.h>
#include <hal_adc_async.h>
#include <hal_usart_sync.h>
#include <hpl_dma.h>



int main(void)
{
	/* Initializes MCU, drivers and middleware*/
	atmel_start_init();
	
	/*Set PWM to turn LED on*/
	pwm_set_parameters(&PWM_0, 1000, 200); 
	pwm_enable(&PWM_0); //output on PB13 (D19) ADC on A11
	
	/*Set up timer to turn LED off*/
	static struct timer_task TIMER_0_task1;
	
	void TIMER_0_task1_cb(const struct timer_task *const timer_task){
		pwm_disable(&PWM_0);	
	} //callback function - inside put what you want to do when timer ends

	TIMER_0_task1.interval = 1000; //This is probably 1*1000ms = 1s, need to check.
	TIMER_0_task1.cb=TIMER_0_task1_cb;
	TIMER_0_task1.mode=TIMER_TASK_ONE_SHOT;
	
	/*Add task and start timer to turn off PWM*/
	timer_add_task(&TIMER_0, &TIMER_0_task1);
	timer_start(&TIMER_0);
	
	//Setup UART COMS 
	usart_sync_enable(&USART_0);
	USART_0.io.write(&USART_0.io, (uint8_t*)"Hello World", 12); //USART Broadcasts over pins D0/D1
	((Sercom *)(USART_0.device.hw))->USART.DATA.reg = 0; // Flush the USART DATA buffer or else DMA combines data with Hello World
	
		/*ADC setup*/
	//static void configure_ADC(void){
		///*Add conversion data*
	//}
	
	
	/*DMA setup*/	
	void dma_complete_callback(struct _dma_resource *dma_res) {
		//_dma_enable_transaction(0, false);
	}
	
	void configure_dma(void) {
		struct _dma_resource* dma_res;
		_dma_init();
		
		/*I think this should set the DMA to look for data in the RESULT register of the ADC
		and send it to the DATA register of SPI*/
		_dma_set_source_address(0, (void*)&(((Adc *)(ADC_0.device.hw))->RESULT.reg));  
		_dma_set_destination_address(0, (uint8_t*)&(((Sercom *)(USART_0.device.hw))->USART.DATA.reg));
		
		//Set how many bytes to read
		_dma_set_data_amount(0, (uint32_t)2);
		//register the application callback after DMA transfer
		_dma_get_channel_resource(&dma_res, 0);
		dma_res->dma_cb.transfer_done = dma_complete_callback;
		
		_dma_set_irq_state(0, DMA_TRANSFER_COMPLETE_CB, true);
		
		/*Enable DMA channel*/
		_dma_enable_transaction(0, false);
	}
	
	adc_async_enable_channel(&ADC_0, 0);
	configure_dma();
	adc_async_start_conversion(&ADC_0);	
	
	
	
	///*Hopefully the DMA is now configured and will read the ADC data once the conversion is started*/
	///*this command turns on the SWTRG. Check the datasheet to see what happens when SWTRG is on. 
	//I think this should make the ADC start converting continuously, and dump everything to the DMA when full*/
	/* Replace with your application code */
	while (1) {
	}
}
