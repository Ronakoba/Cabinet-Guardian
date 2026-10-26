#include <WiFi.h>
#include <HTTPClient.h>
#include <DHT.h>
#include <Wire.h>
#include <LiquidCrystal_I2C.h>

const char* SSID = "YOUR_WIFI_NAME";
const char* PASS = "YOUR_WIFI_PASSWORD";
const char* URL  = "http://YOUR_LAPTOP_IP:8000/reading";
#define DHTPIN 4
#define LEDPIN 5
DHT dht(DHTPIN, DHT11);
LiquidCrystal_I2C lcd(0x27, 16, 2);

void setup() {
  Serial.begin(115200);
  pinMode(LEDPIN, OUTPUT);
  dht.begin();
  lcd.init();
  lcd.backlight();
  lcd.print("Connecting WiFi");
  WiFi.begin(SSID, PASS);
  while (WiFi.status() != WL_CONNECTED) delay(300);
  lcd.clear();
  lcd.print("Guardian ready");
  delay(1000);
}

void loop() {
  delay(2000);
  float t = dht.readTemperature();
  float h = dht.readHumidity();
  if (isnan(t) || isnan(h)) {
    lcd.clear(); lcd.print("Sensor error");
    return;
  }

  String level = "ok", msg = "No server";
  HTTPClient http;
  http.begin(URL);
  http.addHeader("Content-Type", "application/json");
  http.setTimeout(5000);
  int code = http.POST("{\"t\":" + String(t, 1) + ",\"h\":" + String(h, 1) + "}");
  if (code == 200) {
    String r = http.getString();
    int bar = r.indexOf('|');
    level = r.substring(0, bar);
    msg = r.substring(bar + 1);
  }
  Serial.printf("HTTP code: %d\n", code);
  http.end();

  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.printf("T:%.0fC H:%.0f%%", t, h);
  lcd.setCursor(0, 1);
  lcd.print(msg.substring(0, 16));

  digitalWrite(LEDPIN, level == "alert" ? HIGH : LOW);
  if (level == "warn") { digitalWrite(LEDPIN, HIGH); delay(150); digitalWrite(LEDPIN, LOW); }
  Serial.printf("%.1f,%.1f -> %s|%s\n", t, h, level.c_str(), msg.c_str());
}
