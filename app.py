from pyLoraRFM9x import LoRa, ModemConfig
from dotenv import load_dotenv
from pyLoraRFM9x.lora import BROADCAST_ADDRESS
import requests as req
from os import getenv
from time import sleep
import const

NODES = dict()
PREV_NODES = dict()
NUMBER_OF_NODES = 4

#ADDRESSES
#  1 -> gateway
#  2 -> first data node
#  3 -> first water node
#  4 -> second data node
#  5 -> second water node
#  255 -> boradcast 

load_dotenv()
API_KEY = getenv("API_KEY")

API_MAP = {0:getenv("API_KEY1"),
           1:getenv("API_KEY1"),
           2:getenv("API_KEY2"),
           3:getenv("API_KEY2")}

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
            wait_for_all(lora)

            #may need to modify on_recv func because I get two tyes of msg now
            print("Sending waiting time")
            send_wait_time(lora, 15)

            lora.set_mode_sleep()
            send_data_to_cloud()

            PREV_NODES = NODES.copy()
            NODES.clear()

            print("Sleeping...")
            sleep(20)

    except KeyboardInterrupt:
        print("exiting")

#Waits for all nodes to send msg
def wait_for_all(lora:LoRa):
    lora.set_mode_rx()
    
    while len(NODES) < NUMBER_OF_NODES:
        sleep(.1)

#Sends seconds as broadscast for nodes to wait
def send_wait_time(lora:LoRa, seconds:int) -> None:
    lora.set_mode_tx()

    for _ in range(3):
        lora.send_to_wait(seconds, BROADCAST_ADDRESS)
        sleep(.1)

#Sends data to cloud
def send_data_to_cloud():
    if not API_KEY:
        raise ValueError("API key not found")
    
    try:
        for node, data in NODES.items():
            res = req.get(const.URL+API_KEY, params=data)
            res.raise_for_status()
            print(f"node:{node} send data {data}")

    except req.exceptions.RequestException as e:
        print("Error sending data:", e)

#Decodes messages
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

