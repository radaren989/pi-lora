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
NUMBER_OF_NODES = 2

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

API_MAP = {2:[getenv("API_READNODE1"), getenv("API_WRITENODE1")],
           3:[getenv("API_READNODE1"), getenv("API_WRITENODE1")],
           4:[getenv("API_READNODE2"), getenv("API_WRITENODE2")],
           5:[getenv("API_READNODE2"), getenv("API_WRITENODE2")]}

VALVE_API_MAP = {3:(2994571, getenv("API_READVALVE1")),
                 5:(2994572, getenv("API_READVALVE2"))}

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

        channelId, apiKey = VALVE_API_MAP.get(i, (None, None))
        if channelId is None or apiKey is None:
            print(f"manage_valve: missing data for nodeID {i}")
            continue 

        url = const.FETCH_URL.replace("!CHANNEL_HERE!", str(channelId)).replace("!KEY_HERE!", apiKey)
        res = req.get(url).json()

        feeds = res.get("feeds", [])

        if not feeds:
            print(f"manage_valve: no response for nodeId {i}")
            continue

        valve = feeds[0].get("field1")
        print(f"valve{i}: {valve}")

        if valve is None:
            print(f"Valve field is empty")

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
        for i in range(2, max(NODES.keys()) + 1, 2):
            dataNode = NODES.get(i, {})
            waterNode = NODES.get(i+1, {})
            
            mergedData = {**dataNode, **waterNode}

            if not mergedData:
                print(f"No data to send for nodes {i} and {i+1}")
                continue

            api_keys = API_MAP.get(i)
            if not api_keys or api_keys[1] is None:
                print(f"API write key not found for data node {i}")
                continue

            write_key = api_keys[1]
            url = const.UPDATE_URL + write_key
            res = req.get(url, params=mergedData)
            res.raise_for_status()
            print(f"Sent data for node group {i}/{i+1}: {mergedData}")

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
            data = {f"field6":nums[0], # water liter
                    f"field7":nums[1]} # valve status
        else:
            nums = list(message.message.decode('utf-8').split(":"))
            data = {f"field1":nums[0],
                    f"field2":nums[1],
                    f"field3":nums[2],
                    f"field4":nums[3],
                    f"field5":nums[4],}

        NODES[nodeId] = data
        print(f"NodeId: {nodeId}")
        print(f"NodeType: {nodeType}")
        print(message.message)

    except ValueError as e:
        print("Invalid message format", e)


if __name__ == '__main__':
    main()
