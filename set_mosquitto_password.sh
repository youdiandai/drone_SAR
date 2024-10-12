#!/bin/sh

# Set MQTT username and password
echo "Creating MQTT user..."

# Using echo to provide password non-interactively
echo -e "${MQTT_PASSWORD}\n${MQTT_PASSWORD}" | mosquitto_passwd -c /mosquitto/config/passwd $MQTT_USER

# Start mosquitto
echo "Starting Mosquitto..."
exec mosquitto -c /mosquitto/config/mosquitto.conf
