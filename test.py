from pyLoraRFM9x import LoRa, ModemConfig
import const
from time import sleep

# Bu, bir mesaj alındığında çalışacak geri arama fonksiyonu
def on_recv(message):
    global lora
    print("From:", message.header_from)
    print("Received:", message.message)
    print("RSSI: {}; SNR: {}".format(message.rssi, message.snr))
    lora.set_mode_tx()
    lora.send_ack(message.header_from, message.header_to)
# LoRa nesnesini yapılandır
lora = LoRa(**const.LORA_CONST, modem_config=ModemConfig.Bw125Cr45Sf128)
lora.on_recv = on_recv

# Mesajı bekle
try:
    print("Mesaj bekleniyor...")
    while True:
        lora.send("ananı sikeyim senin", 2)
        sleep(0.2)  # Mesaj beklerken kısa süre bekleyin
except KeyboardInterrupt:
    print("Kapanıyor...")

