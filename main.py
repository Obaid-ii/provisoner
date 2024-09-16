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

# Cache for device clients
device_clients: Dict[str, IoTHubDeviceClient] = {}

# Semaphore to limit the number of concurrent tasks
semaphore = asyncio.Semaphore(5)  # Lowered concurrency to reduce connection overload

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
    async with semaphore:
        try:
            # Create or retrieve device and its keys
            device_info = await create_device(device_id)
            primary_key = device_info['primary_key']

            # Get or create device client
            client = await get_device_client(device_id, primary_key)

            # Send data to IoT Hub
            await send_data_to_iot_hub(client, device_id, payload)  # Pass device_id explicitly
            
        except Exception as e:
            logging.error(f"Failed to process payload for {device_id}. Error: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to process data: {e}")

        
"""The get_device_client function retrieves an existing IoT Hub device client or 
creates a new one for the specified device using its connection string."""

async def get_device_client(device_id: str, primary_key: str) -> IoTHubDeviceClient:
    """Retrieve or create a device client for the specified device."""
    if device_id not in device_clients:
        connection_string = f"HostName={IOT_HUB_HOST};DeviceId={device_id};SharedAccessKey={primary_key}"
        try:
            client = IoTHubDeviceClient.create_from_connection_string(connection_string)
            device_clients[device_id] = client
        except Exception as e:
            logging.error(f"Failed to create IoTHubDeviceClient for device {device_id}. Error: {e}")
            raise
    else:
        logging.info(f"Reusing existing client for device {device_id}")
    return device_clients[device_id]

async def send_data_to_iot_hub(client: IoTHubDeviceClient, device_id: str, payload: dict):
    """Send data to IoT Hub for a specific device with retry logic."""
    retries = 3
    for attempt in range(retries):
        try:
            message = Message(json.dumps(payload))
            message.content_type = "application/json"
            message.content_encoding = "utf-8"

            start_time = time.time()
            await asyncio.to_thread(client.send_message, message)
            end_time = time.time()

            latency = (end_time - start_time) * 1000
            logging.info(f"Data sent successfully for {device_id}: Latency: {latency:.2f} ms")

            break  # Exit loop on success

        except Exception as e:
            if attempt < retries - 1:
                logging.warning(f"Send failed, retrying... Attempt {attempt + 1}/{retries}. Error: {e}")
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
            else:
                logging.error(f"Failed to send data after {retries} attempts. Error: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
