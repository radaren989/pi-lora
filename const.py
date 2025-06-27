LORA_CONST = {
    "spi_channel": 0,
    "spi_port": 0,
    "interrupt_pin": 5,
    "my_address": 1,
    "reset_pin": 25,
    "tx_power": 14,
    "acks": False,
    "freq": 433,
    "receive_all": True,
    "crypto": None,
    "default_mode": 0
}

UPDATE_URL = "https://api.thingspeak.com/update?api_key="
FETCH_URL = "https://api.thingspeak.com/channels/!CHANNEL_HERE!/feeds.json?api_key=!KEY_HERE!&results=1"
