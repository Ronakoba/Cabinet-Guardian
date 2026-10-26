# Cabinet Guardian

An ESP32 monitor for a storage cabinet. It reads temperature and humidity, spots unusual changes, and uses **NVIDIA Nemotron on Nebius Token Factory** to explain in plain English what is probably going wrong. The explanation shows on an LCD, and an LED lights up for serious alerts.

**Track:** Physical AI

## How it works
1. The ESP32 reads a DHT11 sensor every 2 seconds and sends the values to a Python server over WiFi.
2. The server keeps a rolling window of readings and flags fast changes or unsafe values.
3. When something is flagged, the server sends the recent readings to Nemotron through the Token Factory API (OpenAI-compatible).
4. The reply (severity + short message) goes back to the ESP32, which shows it on the LCD and LED.

## Where NVIDIA Nemotron and Nebius are used
- Model: [Nemotron model name] on **Nebius Token Factory**
- The model only runs when the rules flag an anomaly, which keeps calls fast and cheap.
- [What Token Factory made easier or faster, in your words]

## Hardware
- ESP32 DevKit V1 (30-pin)
- DHT11 temperature/humidity sensor
- 16x2 I2C LCD
- LED + 220 ohm resistor

| Part | ESP32 pin |
|---|---|
| DHT11 data | GPIO 4 |
| LCD SDA | GPIO 21 |
| LCD SCL | GPIO 22 |
| LED | GPIO 5 |

LCD power goes to VIN (5V), sensor power to 3.3V.

## Setup
**Server**
1. `pip install flask openai`
2. Copy `config.example.py` to `config.py` and fill in your Token Factory API key and Nemotron model name.
3. `python server.py`. It prints `MODE: REAL (Nemotron)`. Without a valid key it runs in a mock mode with canned replies, so you can test the hardware.

**ESP32**
1. In Arduino IDE, install the libraries: DHT sensor library, Adafruit Unified Sensor, LiquidCrystal I2C.
2. Open `firmware/cabinet_guardian/cabinet_guardian.ino` and set your WiFi name, password, and the server's IP address.
3. Select board "ESP32 Dev Module" and upload.

The ESP32 and the computer running the server must be on the same 2.4 GHz network.

## Feedback on the tools
[Fill in after using Token Factory and Nemotron]

## License
MIT
