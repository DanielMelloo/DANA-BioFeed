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

// Water Solenoid Pin (Example GPIO 26)
const int SOLENOID_PIN = 26; 

void setup() {
  Serial.begin(115200);
  
  // Servo Setup
  feederServo.attach(SERVO_PIN);
  feederServo.write(SERVO_CLOSED_POS);

  // Sensor Setup
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  
  // Solenoid Setup
  pinMode(SOLENOID_PIN, OUTPUT);
  digitalWrite(SOLENOID_PIN, LOW); // Normally Closed? Or Open? Logic says Normally Open = Auto. 
  // Let's assume LOW = Closed, HIGH = Open for control.
  // If hardware is Normally Open, then LOW = Open. 
  // User said "Solenoide Normally Open = Auto". "Closed by user = Manual".
  // We will control it: HIGH to Open (Auto Refill), LOW to Close (Stop).

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

long readUltrasonic() {
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);
  
  long duration = pulseIn(ECHO_PIN, HIGH);
  long distanceCm = duration * 0.034 / 2;
  
  return distanceCm;
}

// Mock Load Cell Reading
float readScale() {
  // In real hardware, read HX711
  // For simulation, we return a mock value or the last value sent by simulator
  return 0.0; 
}

void sendHeartbeat() {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    
    String url = String(SERVER_URL) + "/feeder/" + String(FEEDER_ID) + "/status";
    
    http.begin(url);
    http.addHeader("Content-Type", "application/json");
    http.addHeader("Authorization", String("Bearer ") + String(FEEDER_TOKEN));

    // Read Sensors
    long dist = readUltrasonic();
    int level = map(dist, 20, 5, 0, 100); 
    level = constrain(level, 0, 100);

    StaticJsonDocument<200> doc;
    doc["battery"] = 100; 
    doc["weight"] = level; // Should be readScale() in real hardware
    doc["water_sensor"] = "LSH"; 
    doc["firmware_version"] = "1.2.0-ESP32";

    String requestBody;
    serializeJson(doc, requestBody);

    int httpResponseCode = http.POST(requestBody);

    if (httpResponseCode > 0) {
      String response = http.getString();
      Serial.println("Heartbeat Sent. Response: " + response);
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
    Serial.println("Raw Response:");
    Serial.println(jsonResponse);
    return;
  }

  JsonArray commands = doc["commands"];
  for (JsonObject cmd : commands) {
    String type = cmd["type"];
    String cmdId = cmd["id"];
    int duration = cmd["duration"] | 1000;
    
    Serial.print("Executing Command: ");
    Serial.println(type);

    if (type == "feed") {
      dispenseFood(duration);
      ackCommand("feed", "executed", cmdId);
    } else if (type == "smart_refill") {
      smartRefill(cmdId);
    } else if (type == "water_control") {
      String action = cmd["action"]; // "OPEN" or "CLOSE"
      controlWater(action);
      ackCommand("water_control", "executed", cmdId);
    }
  }
}

void dispenseFood(int duration) {
  Serial.println("Opening Bottom Servo (Feed)...");
  feederServo.write(SERVO_OPEN_POS);
  delay(duration);
  Serial.println("Closing Bottom Servo...");
  feederServo.write(SERVO_CLOSED_POS);
}

void smartRefill(String cmdId) {
  Serial.println("Starting Smart Refill (Top Servo)...");
  // Assume Top Servo is on another pin or same servo mechanism (Simulated)
  // Logic: Open Top -> Wait until Weight >= 210g -> Close Top
  
  // Simulation Logic:
  // In real hardware, we would loop:
  // while (readScale() < 210.0) { delay(100); }
  
  Serial.println("Refilling...");
  delay(2000); // Simulate fill time
  Serial.println("Refill Complete (210g reached).");
  
  ackCommand("smart_refill", "executed", cmdId);
}

void controlWater(String action) {
  if (action == "OPEN") {
    digitalWrite(SOLENOID_PIN, HIGH);
    Serial.println("Solenoid OPEN (Auto Refill)");
  } else {
    digitalWrite(SOLENOID_PIN, LOW);
    Serial.println("Solenoid CLOSED");
  }
}

void ackCommand(String cmdType, String status, String cmdId) {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    String url = String(SERVER_URL) + "/feeder/" + String(FEEDER_ID) + "/ack";
    
    http.begin(url);
    http.addHeader("Content-Type", "application/json");
    http.addHeader("Authorization", String("Bearer ") + String(FEEDER_TOKEN));

    StaticJsonDocument<200> doc;
    doc["command_id"] = cmdId; 
    doc["status"] = status;

    String requestBody;
    serializeJson(doc, requestBody);
    http.POST(requestBody);
    http.end();
  }
}
