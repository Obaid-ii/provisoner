import logging
import time
#import uuid
CONNECTION_STRING =  "HostName=iothubdevuae.azure-devices.net;SharedAccessKeyName=iothubowner;SharedAccessKey=TgNmv49DIduLOsnHU7ccaESSOcXnpKu9UAIoTOMlm0s="
IOT_HUB_HOST =  "iothubdevuae.azure-devices.net"
PAYLOAD_INTERVAL =   10 * 1000 # seconds
MQTT_PORT =  8883
TEMP_MAX =   28
TEMP_MIN =   25
TEMP_DP =   2
TokenValidity_Time =    3600 # seconds 
last_sent_time =         int(time.time() * 1000)

