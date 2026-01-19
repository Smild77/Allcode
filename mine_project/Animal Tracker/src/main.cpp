/* RECEIVER GATEWAY (HOUSE)
   รับ NRF24 -> ต่อ WiFi -> ส่งเข้า Node-RED (MQTT)
*/
#include <Arduino.h>
#include <SPI.h>
#include <RF24.h>
#include <WiFi.h>
#include <PubSubClient.h>
// --------- ตั้งค่าตรงนี้ -----------
const char* ssid = "PL";
const char* password = "00000000";
// -------------------------

const char* mqtt_server = "broker.hivemq.com"; // Broker สาธารณะ (ใช้ง่ายสุด)
const char* mqtt_topic = "project/outdoor/location"; // หัวข้อที่จะส่งไป Node-RED

#define CE_PIN   4
#define CSN_PIN  5

RF24 radio(CE_PIN, CSN_PIN);
WiFiClient espClient;
PubSubClient client(espClient);

const byte address[6] = "00001"; // ต้องตรงกับตัวส่ง

struct Data_Package {
  float lat;
  float lng;
  byte status;
};
Data_Package data;

void setup_wifi() {
  delay(10);
  Serial.println();
  Serial.print("Connecting to WiFi: ");
  Serial.println(ssid);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi Connected!");
}

void reconnect() {
  while (!client.connected()) {
    Serial.print("Connecting to MQTT...");
    String clientId = "ESP32-Gateway-" + String(random(0xffff), HEX);
    if (client.connect(clientId.c_str())) {
      Serial.println("Connected!");
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      delay(5000);
    }
  }
}

void setup() {
  Serial.begin(115200);
  if (!radio.begin()) {
    Serial.println("❌ NRF24 Error!");
    while (1);
  }
  radio.openReadingPipe(0, address);
  radio.setPALevel(RF24_PA_MAX); // ใช้ MAX เพื่อรับไกลๆ
  radio.setDataRate(RF24_250KBPS); // ต้องตรงกับตัวส่ง
  radio.startListening();

  setup_wifi();
  client.setServer(mqtt_server, 1883);
}

void loop() {
  if (!client.connected()) reconnect();
  client.loop();

  if (radio.available()) {
    radio.read(&data, sizeof(Data_Package));
    Serial.print("Received -> Lat: "); Serial.print(data.lat, 6);
    Serial.print(" Lng: "); Serial.println(data.lng, 6);
    String msg = "{\"lat\":";
    msg += String(data.lat, 6);
    msg += ",\"lng\":";
    msg += String(data.lng, 6);
    msg += "}";
    
    // 3. ยิงขึ้น MQTT
    client.publish(mqtt_topic, msg.c_str());
  }
}