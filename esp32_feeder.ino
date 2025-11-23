#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <ESP32Servo.h>

// ================= CONFIGURATIONS =================
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";

// Backend Server URL (Use your PC IP if local, e.g., http://192.168.1.100:5000)
const char* serverUrl = "http://192.168.1.100:5000/api";

// Feeder Token (Get this from the dashboard or register endpoint)
const char* feederToken = "YOUR_FEEDER_TOKEN";
const int feederId = 1; // Your Feeder ID

// Servo Configuration
Servo myservo;
const int servoPin = 13;
const int closedPos = 0;
const int openPos = 90;

// Timing
unsigned long lastCheck = 0;
const long checkInterval = 10000; // Check every 10 seconds

void setup() {
  Serial.begin(115200);
  
  // Servo Setup
  myservo.attach(servoPin);
  myservo.write(closedPos);

  // WiFi Setup
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.println("Connecting to WiFi...");
  }
  Serial.println("Connected to WiFi");
}

void loop() {
  unsigned long currentMillis = millis();

  if (currentMillis - lastCheck >= checkInterval) {
    lastCheck = currentMillis;
    
    if (WiFi.status() == WL_CONNECTED) {
      checkCommands();
      reportStatus();
    }
  }
}

void checkCommands() {
  HTTPClient http;
  String url = String(serverUrl) + "/feeder/" + String(feederId) + "/command";
  
  http.begin(url);
  http.addHeader("Authorization", String("Bearer ") + String(feederToken));
  
  int httpResponseCode = http.GET();
  
  if (httpResponseCode == 200) {
    String payload = http.getString();
    DynamicJsonDocument doc(1024);
    deserializeJson(doc, payload);
    
    JsonArray commands = doc["commands"];
    for (JsonObject cmd : commands) {
      String type = cmd["type"];
      if (type == "feed") {
        int duration = cmd["duration"];
        feed(duration);
        sendAck(cmd["id"], "executed"); // Assuming cmd has ID, or just generic ack
      }
    }
  }
  http.end();
}

void feed(int durationMs) {
  Serial.println("Feeding...");
  myservo.write(openPos);
  delay(durationMs);
  myservo.write(closedPos);
  
  // Log event to server
  logEvent("auto", durationMs);
}

void reportStatus() {
  HTTPClient http;
  String url = String(serverUrl) + "/feeder/" + String(feederId) + "/status";
  
  http.begin(url);
  http.addHeader("Content-Type", "application/json");
  http.addHeader("Authorization", String("Bearer ") + String(feederToken));
  
  StaticJsonDocument<200> doc;
  doc["health"] = "good";
  doc["firmware_version"] = "1.0.0";
  
  String requestBody;
  serializeJson(doc, requestBody);
  
  http.POST(requestBody);
  http.end();
}

void logEvent(String action, int duration) {
  HTTPClient http;
  String url = String(serverUrl) + "/feeder/" + String(feederId) + "/log";
  
  http.begin(url);
  http.addHeader("Content-Type", "application/json");
  http.addHeader("Authorization", String("Bearer ") + String(feederToken));
  
  StaticJsonDocument<200> doc;
  doc["action"] = action;
  doc["duration_ms"] = duration;
  
  String requestBody;
  serializeJson(doc, requestBody);
  
  http.POST(requestBody);
  http.end();
}

void sendAck(String cmdId, String status) {
  HTTPClient http;
  String url = String(serverUrl) + "/feeder/" + String(feederId) + "/ack";
  
  http.begin(url);
  http.addHeader("Content-Type", "application/json");
  http.addHeader("Authorization", String("Bearer ") + String(feederToken));
  
  StaticJsonDocument<200> doc;
  doc["command_id"] = cmdId;
  doc["status"] = status;
  
  String requestBody;
  serializeJson(doc, requestBody);
  
  http.POST(requestBody);
  http.end();
}
