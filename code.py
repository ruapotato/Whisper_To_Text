#For a adafruit circuitpython feather
import board
from adafruit_ble import BLERadio
from adafruit_ble.advertising.standard import ProvideServicesAdvertisement
from adafruit_ble.services.nordic import UARTService
from digitalio import DigitalInOut, Direction, Pull
import time

# LED setup
led = DigitalInOut(board.LED)
led.direction = Direction.OUTPUT

# Button setup
button = DigitalInOut(board.D5)  # Adjust this pin as needed for your specific board
button.direction = Direction.INPUT
button.pull = Pull.UP

# Bluetooth setup
ble = BLERadio()
uart = UARTService()
advertisement = ProvideServicesAdvertisement(uart)

print("Bluetooth device name:", ble.name)

while True:
    ble.start_advertising(advertisement)
    print("Waiting to connect")
    while not ble.connected:
        pass
    print("Connected")
    
    button_state = False
    while ble.connected:
        current_state = not button.value  # Button is pulled up, so press gives False
        
        if current_state != button_state:
            button_state = current_state
            if button_state:
                print("Button pressed")
                uart.write("START\n")
                print("UART: Sent START")  # Debug print
                led.value = True
            else:
                print("Button released")
                uart.write("STOP\n")
                print("UART: Sent STOP")  # Debug print
                led.value = False
        
        time.sleep(0.01)  # Small delay to avoid excessive polling

    print("Disconnected")
