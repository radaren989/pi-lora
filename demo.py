import requests
import random
import time

# ThingSpeak API parameters
API_KEY = "E444A1NVQ09VG7R5"  # Replace with your ThingSpeak Write API key
THINGSPEAK_URL = "https://api.thingspeak.com/update"

def send_random_data_to_thingspeak():
    """
    Generates random values for 7 fields and sends them to ThingSpeak.
    """
    # Generate random values for each field (e.g., between 0 and 100)
    field_values = [random.uniform(0, 100) for _ in range(7)]
    
    payload = {
        'api_key': API_KEY,
        'field1': field_values[0],
        'field2': field_values[1],
        'field3': field_values[2],
        'field4': field_values[3],
        'field5': field_values[4],
        'field6': field_values[5],
        'field7': field_values[6],
    }
    
    response = requests.post(THINGSPEAK_URL, data=payload)
    
    if response.status_code == 200:
        print("Data successfully sent to ThingSpeak.")
        print(f"Sent values: {field_values}")
    else:
        print(f"Failed to send data. HTTP status code: {response.status_code}")
        print("Response:", response.text)

# Example usage
if __name__ == "__main__":
    while True:
        try:
            send_random_data_to_thingspeak()
            time.sleep(15)  # ThingSpeak allows updates every 15 seconds
        except Exception as e:
            print(f"Error: {e}")

