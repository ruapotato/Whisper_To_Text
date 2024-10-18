import asyncio
import time
import threading
import numpy as np
import sounddevice as sd
import requests
from bleak import BleakClient, BleakScanner
import subprocess

TRUSTED_DEVICE = "CIRCUITPY6ef3"
UART_SERVICE_UUID = "6e400001-b5a3-f393-e0a9-e50e24dcca9e"
UART_TX_CHAR_UUID = "6e400003-b5a3-f393-e0a9-e50e24dcca9e"

# Audio recording configuration
SAMPLE_RATE = 16000
SERVER_URL = 'http://localhost:5000/transcribe'

# Global variables
recording = False
audio_data = []
last_event = time.time()

def record_audio():
    global recording, audio_data
    audio_data = []
    
    def callback(indata, frames, time, status):
        if recording:
            audio_data.append(indata.copy())

    with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, callback=callback):
        while recording:
            sd.sleep(100)

def send_audio_to_server(audio):
    try:
        response = requests.post(SERVER_URL, files={'audio': audio.tobytes()})
        if response.status_code == 200:
            transcription = response.json()['transcription']
            print(f"Transcription: {transcription}")
            type_transcription(transcription)
        else:
            print(f"Error: Server returned status code {response.status_code}")
    except Exception as e:
        print(f"Error sending audio to server: {str(e)}")

def type_transcription(text):
    try:
        # Use xdotool to type the transcription
        subprocess.run(['xdotool', 'type', text], check=True)
        print("Transcription typed successfully")
    except subprocess.CalledProcessError as e:
        print(f"Error typing transcription: {e}")
    except FileNotFoundError:
        print("Error: xdotool not found. Please install xdotool.")

def uart_data_handler(sender, data):
    global recording, last_event
    raw_cmd = data.decode().strip()
    if raw_cmd == "START":
        print("Recording started...")
        recording = True
        threading.Thread(target=record_audio).start()
    elif raw_cmd == "STOP":
        print("Recording stopped. Transcribing...")
        recording = False
        if audio_data:
            audio = np.concatenate(audio_data, axis=0)
            send_audio_to_server(audio)
        else:
            print("No audio data recorded.")
    else:
        # Handle other data if needed (e.g., acceleration and gyro data)
        print(f"Received data: {raw_cmd}")
    last_event = time.time()

async def run_ble_client(address):
    async with BleakClient(address) as client:
        print(f"Connected: {client.is_connected}")
        await client.start_notify(UART_TX_CHAR_UUID, uart_data_handler)
        print("Notification started")

        while True:
            if not client.is_connected:
                print("Device disconnected")
                break
            await asyncio.sleep(1)

async def main():
    while True:
        try:
            print("Scanning for the trusted device...")
            device = await BleakScanner.find_device_by_name(TRUSTED_DEVICE)
            if device:
                print(f"Found trusted device: {device.name} ({device.address})")
                await run_ble_client(device.address)
            else:
                print(f"Trusted device '{TRUSTED_DEVICE}' not found.")
            
            print("Retrying in 5 seconds...")
            await asyncio.sleep(5)
        except Exception as e:
            print(f"An error occurred: {str(e)}")
            print("Retrying in 5 seconds...")
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())
