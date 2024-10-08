import logging
import asyncio
from db_util import start_postgres_connection
from iothub_util import registry_manager

logging.basicConfig(level=logging.INFO)

async def create_device(device_id: str):
    """Asynchronously creates or retrieves a device from PostgreSQL or IoT Hub."""
    conn = start_postgres_connection()
    if not conn:
        logging.error("Database connection failed.")
        return None

    cursor = conn.cursor()

    try:
        # Check if device already exists in PostgreSQL
        cursor.execute("SELECT * FROM devices WHERE device_id = %s;", (device_id,))
        device_info = cursor.fetchone()

        if device_info:
            logging.info(f"Device {device_id} already exists in PostgreSQL.")
            return {
                'device_id': device_info[0],
                'primary_key': device_info[1],
                'secondary_key': device_info[2]
            }

        # Check IoT Hub for existing device
        try:
            device = registry_manager.get_device(device_id)
            logging.info(f"Device {device_id} already exists in IoT Hub.")
            return {
                'device_id': device.device_id,
                'primary_key': device.authentication.symmetric_key.primary_key,
                'secondary_key': device.authentication.symmetric_key.secondary_key
            }
        except Exception as e:
            logging.error(f"Device not found in IoT Hub. Error: {str(e)}. Creating new device.")
            device = registry_manager.create_device_with_sas(
                device_id=device_id, primary_key=None, secondary_key=None, status="enabled"
            )
            logging.info(f"New Device created in IoT Hub. ID: {device.device_id}, Primary Key: {device.authentication.symmetric_key.primary_key}")

            # Insert the new device into PostgreSQL
            try:
                cursor.execute(
                    "INSERT INTO devices (device_id, primary_key, secondary_key) VALUES (%s, %s, %s);",
                    (device.device_id, device.authentication.symmetric_key.primary_key, device.authentication.symmetric_key.secondary_key)
                )
                conn.commit()
                logging.info(f"Device {device.device_id} inserted into PostgreSQL successfully.")
            except Exception as db_error:
                conn.rollback()
                logging.error(f"Error inserting device into PostgreSQL: {db_error}")
                raise db_error

            return {
                'device_id': device.device_id,
                'primary_key': device.authentication.symmetric_key.primary_key,
                'secondary_key': device.authentication.symmetric_key.secondary_key
            }

    finally:
        # Ensure that cursor and connection are always closed
        if cursor:
            cursor.close()
        if conn:
            conn.close()

