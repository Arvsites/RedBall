#include <WiFiClient.h>
#include <ESP8266WebServer.h>
#include <ESP8266WiFi.h>
#include <WiFiUDP.h>

const char* ssid = "mudorobot";
const char* password = "mudoparol123";
WiFiUDP udp;


void setup() {
  WiFi.softAP(ssid, password);
  Serial.begin(115200);
  IPAddress IP = WiFi.softAPIP();
  udp.begin(1234);  // Порт, на котором NodeMCU будет прослушивать
  Serial.println("UDP server started");
}

void loop() {
  int packetSize = udp.parsePacket();

  if (packetSize) {
    char packetData[255];
    udp.read(packetData, packetSize);
    Serial.println(packetData[0]);
  }
}
