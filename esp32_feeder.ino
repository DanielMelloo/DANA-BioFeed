#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <ESP32Servo.h>

// ================= CONFIGURATIONS =================
const char* WIFI_SSID = "YOUR_WIFI_SSID";
const char* WIFI_PASS = "YOUR_WIFI_PASSWORD";

// API Configuration
const char* SERVER_URL = "http://biofeed.danielmello.store/api"; // Use HTTP for simplicity, or HTTPS with ClientSecure
const char* FEEDER_TOKEN = "YOUR_DEVICE_TOKEN_HERE"; // Get this from the Web Dashboard
const char* FEEDER_ID = "2";       // Get this from the Web Dashboard

// Hardware Pins
const int SERVO_PIN = 13;
const int TRIG_PIN = 12; // Optional: Ultrasonic Trig
const int ECHO_PIN = 14; // Optional: Ultrasonic Echo

// Settings
const int CHECK_INTERVAL = 5000; // Check for commands every 5 seconds
const int SERVO_OPEN_POS = 90;
const int SERVO_CLOSED_POS = 0;

// ================= GLOBALS =================
Servo feederServo;
unsigned long lastCheckTime = 0;

void setup() {
  Serial.begin(115200);
  
  // Servo Setup
  feederServo.attach(SERVO_PIN);
  feederServo.write(SERVO_CLOSED_POS);

  // WiFi Setup
  connectWiFi();
}

void loop() {
  // Reconnect WiFi if lost
  if (WiFi.status() != WL_CONNECTED) {
    connectWiFi();
  }

  // Heartbeat & Command Check
  if (millis() - lastCheckTime > CHECK_INTERVAL) {
    lastCheckTime = millis();
    sendHeartbeat();
  }
}

void connectWiFi() {
  Serial.print("Connecting to WiFi");
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi Connected!");
  Serial.print("IP: ");
  Serial.println(WiFi.localIP());
}

void sendHeartbeat() {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    
    // Construct URL: /api/feeder/<id>/status
    String url = String(SERVER_URL) + "/feeder/" + String(FEEDER_ID) + "/status";
    
    http.begin(url);
    http.addHeader("Content-Type", "application/json");
    http.addHeader("Authorization", String("Bearer ") + String(FEEDER_TOKEN));

    // Create JSON Payload
    StaticJsonDocument<200> doc;
    doc["battery"] = 100; // Mock battery
    doc["weight"] = 0;    // Mock weight (or read load cell)
    doc["water_sensor"] = "LSH"; // Mock water sensor
    doc["firmware_version"] = "1.0.0-ESP32";

    String requestBody;
    serializeJson(doc, requestBody);

    int httpResponseCode = http.POST(requestBody);

    if (httpResponseCode > 0) {
      String response = http.getString();
      Serial.println("Heartbeat Sent. Response: " + response);
      
      // Parse Response for Commands
      processResponse(response);
    } else {
      Serial.print("Error on sending POST: ");
      Serial.println(httpResponseCode);
    }

    http.end();
  }
}

void processResponse(String jsonResponse) {
  StaticJsonDocument<1024> doc;
  DeserializationError error = deserializeJson(doc, jsonResponse);

  if (error) {
    Serial.print("deserializeJson() failed: ");
    Serial.println(error.c_str());
    return;
  }

  // Check for commands array
  JsonArray commands = doc["commands"];
  for (JsonObject cmd : commands) {
    String type = cmd["type"];
    int duration = cmd["duration"] | 1000;
    
    Serial.print("Executing Command: ");
    Serial.println(type);

    if (type == "feed") {
      dispenseFood(duration);
      ackCommand("feed", "executed");
    } else if (type == "refill") {
      // Handle refill logic (e.g., open top gate)
      ackCommand("refill", "executed");
    }
  }
}

void dispenseFood(int duration) {
  Serial.println("Opening Servo...");
  feederServo.write(SERVO_OPEN_POS);
  delay(duration);
  Serial.println("Closing Servo...");
  feederServo.write(SERVO_CLOSED_POS);
}

void ackCommand(String cmdType, String status) {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    String url = String(SERVER_URL) + "/feeder/" + String(FEEDER_ID) + "/ack";
    
    http.begin(url);
    http.addHeader("Content-Type", "application/json");
    http.addHeader("Authorization", String("Bearer ") + String(FEEDER_TOKEN));

    StaticJsonDocument<200> doc;
    doc["command_id"] = "esp-ack"; // In real scenario, pass the ID received
    doc["status"] = status;

    String requestBody;
    serializeJson(doc, requestBody);
    http.POST(requestBody);
    http.end();
  }
}
