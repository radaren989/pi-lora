from pyLoraRFM9x import LoRa, ModemConfig
# from pyLoraRFM9x.lora import BROADCAST_ADDRESS, FLAGS_REQ_ACK
from dotenv import load_dotenv
import requests as req
from os import getenv
from time import sleep
import const

NODES = dict()
PREV_NODES = dict()
NUMBER_OF_NODES = 1

def setup():
    # Configure Lora module
    lora = LoRa(**const.LORA_CONST, modem_config=ModemConfig.Bw125Cr45Sf128)
    lora.on_recv = on_recv
    
    return lora

def main():
    lora = setup()
    try:
        while True:
            print("Waking up...")
            lora.set_mode_rx()
            while len(NODES) < NUMBER_OF_NODES:
                sleep(.1)
            

            lora.set_mode_sleep()
            send_data_to_cloud()
            PREV_NODES = NODES.copy()
            NODES.clear()
            print("Sleeping...")
            sleep(20)

    except KeyboardInterrupt:
        print("exiting")

def send_data_to_cloud():
    load_dotenv()
    api_key = getenv("API_KEY")
    if not api_key:
        raise ValueError("API key not found")
    
    try:
        for node, data in NODES.items():
            res = req.get(const.URL+api_key, params=data)
            res.raise_for_status()
            print(f"node:{node} send data {data}")

    except req.exceptions.RequestException as e:
        print("Error sending data:", e)
    
def on_recv(message):
    global NODES
    try:
        nums = list(map(int, message.message.decode('utf-8').split(":")))
        data = {f"field{i+1}": v for i, v in enumerate(nums)}
        
        NODES[message.header_from] = data
        print(message)
        
    except ValueError as e:
        print("Invalid message format", e)


if __name__ == '__main__':
    main()

