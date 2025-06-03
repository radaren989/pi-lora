from pyLoraRFM9x import LoRa, ModemConfig
from dotenv import load_dotenv
from pyLoraRFM9x.constants import FLAGS_REQ_ACK
from pyLoraRFM9x.lora import BROADCAST_ADDRESS
import requests as req
import json
from os import getenv
from time import sleep
import const

NODES = dict()
PREV_NODES = dict()
NUMBER_OF_NODES = 1

#ADDRESSES
#  1 -> gateway (this machine)
#  2 -> first data node
#  3 -> first water node
#  4 -> second data node
#  5 -> second water node
#  255 -> boradcast 

#Header flag
# 0x00 -> data node msg
# 0x04 -> valve status send
# 0x02 -> wait time

load_dotenv()

API_MAP = {2:[getenv("API_KEYREAD1"), getenv("API_KEYWRITE1")],
           3:[getenv("API_KEYREAD1"), getenv("API_KEYWRITE1")],
           4:[getenv("API_KEYREAD2"), getenv("API_KEYWRITE2")],
           5:[getenv("API_KEYREAD2"), getenv("API_KEYWRITE2")]}

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

            print("Send Valve Request")
            manage_valve(lora)
            sleep(1)

            print("Sending waiting time")
            send_wait_time(lora, 15)

            lora.set_mode_sleep()
            send_data_to_cloud()

            PREV_NODES = NODES.copy()
            NODES.clear()

            print("Sleeping...")
            sleep(13)

    except KeyboardInterrupt:
        print("exiting")


def manage_valve(lora:LoRa):
    for i in NODES.keys():
        if i % 2 == 0:
            continue

        api_keys = API_MAP.get(i)
        if api_keys is None:
            print(f"manage_valve: API_KEYS is none for nodeID {i}")
            continue
        

        api_key = api_keys[1] # read key
        if api_key is None:
            print(f"manage_valve: read API_KEY is none for nodeID {i}")
            continue

        url = const.FETCH_URL.replace("!KEY_HERE!", api_key)
        res = req.get(url).json()
        feeds = res.get("feeds", [])

        if not feeds:
            print(f"manage_valve: no response for nodeId {i}")
            continue

        valve = feeds[0].get("field8")
        print(f"valve: {valve}")
        if not lora.send_to_wait(valve, i, header_flags=0x04):
            print(f"manage_valve: valve status could not send to water node {i}")

        print(f"manage_valve: valve status sent to water node {i}")
        

#Waits for all nodes to send msg
def wait_for_all(lora:LoRa):
    lora.set_mode_rx()
    
    while len(NODES) < NUMBER_OF_NODES:
        sleep(.1)

#Sends seconds as broadscast for nodes to wait
def send_wait_time(lora:LoRa, seconds:int) -> None:
    lora.set_mode_tx()

    lora.send_to_wait(str(seconds), BROADCAST_ADDRESS, header_flags=0x02)

#Sends data to cloud
def send_data_to_cloud():
    if not API_MAP.values():
        raise ValueError("API key not found")
    
    try:
        for nodeId, data in NODES.items():
            api_keys = API_MAP.get(nodeId)
            if api_keys is None:
                print(f"NodeId  {nodeId} not in API_MAP")
                continue

            api_key = api_keys[0]
            if api_key is None:
                print(f"NodeId {nodeId} does not have Read API in API_MAP")
                continue

            url = const.UPDATE_URL + api_key
            res = req.get(url, params=data)
            res.raise_for_status()
            print(f"node:{nodeId} send data {data}")

    except req.exceptions.RequestException as e:
        print("Error sending data:", e)

#Decodes messages
def on_recv(message):
    global NODES
    try:
        nodeId = message.header_from

        nodeType = nodeId % 2 # 0 -> data 1-> water

        nums = list()
        data = {}
        if nodeType:
            nums = list(message.message.decode('utf-8').split(":"))
            data = {f"field6:":nums[0], # water liter
                    f"field7:":nums[1]} # valve status
        else:
            nums = list(message.message.decode('utf-8').split(":"))
            data = {f"field1:":nums[0],
                    f"field2:":nums[1],
                    f"field3:":nums[2],
                    f"field4:":nums[3],
                    f"field5:":nums[4],}

        NODES[nodeId] = data
        print(f"NodeId: {nodeId}")
        print(f"NodeType: {nodeType}")
        print(message.message)

    except ValueError as e:
        print("Invalid message format", e)


if __name__ == '__main__':
    main()

