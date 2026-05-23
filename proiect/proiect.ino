#include <WiFi.h>
#include <HTTPClient.h>

#define PIR_PIN 14
#define LED_PIN 33

// Schimbă cu datele rețelei tale WiFi
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";

// IP-ul PC-ului unde rulează Flask (aceeași rețea WiFi)
const char* serverUrl = "http://192.168.x.x:5000/motion";

int lastMotion = LOW;

void trimiteDate(bool motion);

void setup() {
  Serial.begin(115200);

  pinMode(PIR_PIN, INPUT_PULLDOWN);
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);

  Serial.println("Conectare la WiFi...");
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\nWiFi conectat!");
  Serial.println(WiFi.localIP());

  Serial.println("Calibrare PIR 30 secunde...");
  delay(30000);
  Serial.println("Senzor PIR pregatit.");
}

void loop() {
  int miscare = digitalRead(PIR_PIN);

  if (miscare == HIGH) {
    digitalWrite(LED_PIN, HIGH);
  } else {
    digitalWrite(LED_PIN, LOW);
  }

  // Trimite la server doar cand se schimba starea
  if (miscare != lastMotion) {
    lastMotion = miscare;

    if (miscare == HIGH) {
      Serial.println(">> Miscare detectata!");
      trimiteDate(true);
    } else {
      Serial.println("Fara miscare.");
      trimiteDate(false);
    }
  }

  delay(100);
}

void trimiteDate(bool motion) {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;

    http.begin(serverUrl);
    http.addHeader("Content-Type", "application/json");

    String jsonData = "{\"device_id\":\"esp32_pir_1\",\"motion\":" + String(motion ? "true" : "false") + "}";

    int httpResponseCode = http.POST(jsonData);

    Serial.print("HTTP Response: ");
    Serial.println(httpResponseCode);

    String response = http.getString();
    Serial.println(response);

    if (response.indexOf("\"led_command\":true") >= 0) {
      digitalWrite(LED_PIN, HIGH);
      Serial.println("Comanda primita de la server: LED ON");
    } else if (response.indexOf("\"led_command\":false") >= 0) {
      digitalWrite(LED_PIN, LOW);
      Serial.println("Comanda primita de la server: LED OFF");
    }

    http.end();
  }
}
