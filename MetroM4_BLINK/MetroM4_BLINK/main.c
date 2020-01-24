#include <atmel_start.h>

int main(void)
{
	/* Initializes MCU, drivers and middleware */
	atmel_start_init();
	uint8_t LED_PIN = GPIO(GPIO_PORTB, 1);
	gpio_set_pin_direction(LED_PIN, GPIO_DIRECTION_OUT);
	/* Replace with your application code */
	while (1) {
		gpio_toggle_pin_level(LED_PIN);
		delay_ms(1000);
	}
	// IT WORKS!!! Tested with PB01 11/29 with JLINK
}
