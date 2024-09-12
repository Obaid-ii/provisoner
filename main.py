from fastapi import FastAPI, HTTPException, Request
import json
import time
import logging
import asyncio
from db_util import *
from iothub_util import *
from azure.iot.device import IoTHubDeviceClient, Message
from typing import Dict
from create_devices import *  # Import the create_device function

app = FastAPI()

# Configure logging
logging.basicConfig(level=logging.INFO)

@app.on_event("startup")
async def startup_event():
    logging.info("Application startup: Preparing to send data to IoT Hub.")

@app.on_event("shutdown")
def shutdown_event():
    logging.info("Application shutdown: Closing database connection.")
    conn = start_postgres_connection()
    close_postgres_connection(conn)

@app.post("/receive-data")
async def receive_data(request: Request):
    try:
        payload = await request.json()
        device_id = payload.get("DeviceID")
        if not device_id:
            raise HTTPException(status_code=400, detail="DeviceID is missing in the payload.")

        # Process the received payload
        await process_payload(device_id, payload)
        return {"status": "success", "message": "Device processed successfully."}
    except Exception as e:
        logging.error(f"Failed to process payload. Error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process data: {e}")

async def process_payload(device_id: str, payload: dict) -> None:
    """Process the received payload, check/create device, and send data to IoT Hub."""
    try:
        # Create or retrieve device and its keys
        device_info = await create_device(device_id)
        primary_key = device_info['primary_key']

        # Send data to IoT Hub
        if primary_key:
            await send_data_to_iot_hub(device_id, payload, primary_key)

    except Exception as e:
        logging.error(f"Failed to process payload for {device_id}. Error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process data: {e}")

async def send_data_to_iot_hub(device_id: str, payload: dict, primary_key: str):
    """Send data to IoT Hub for a specific device."""
    try:
        connection_string = f"HostName={IOT_HUB_HOST};DeviceId={device_id};SharedAccessKey={primary_key}"
        client = IoTHubDeviceClient.create_from_connection_string(connection_string)

        message = Message(json.dumps(payload))
        message.content_type = "application/json"
        message.content_encoding = "utf-8" 

        start_time = time.time()
        await asyncio.to_thread(client.send_message, message)
        end_time = time.time()

        latency = (end_time - start_time) * 1000
        logging.info(f"Data sent successfully for {device_id}: Latency: {latency:.2f} ms")

    except Exception as e:
        logging.error(f"Failed to send data for {device_id}. Error: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000)
