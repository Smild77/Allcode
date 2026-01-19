/* SENDER CODE (ANIMAL) - Custom GPS Pins
   GPS RX=23, TX=22 | NRF24 MOSI=27
*/
#include <Arduino.h>
#include <SPI.h>
#include <RF24.h>
#include <TinyGPS++.h>

// --- ตั้งค่าขา GPS ตามที่คุณขอ ---
#define GPS_RX_PIN 22 // ต่อกับขา TX ของโมดูล GPS
#define GPS_TX_PIN 23 // ต่อกับขา RX ของโมดูล GPS

// --- ตั้งค่าขา NRF24 ---
#define CE_PIN   4
#define CSN_PIN  5

// --- Object Setup ---
RF24 radio(CE_PIN, CSN_PIN);
TinyGPSPlus gps;
HardwareSerial gpsSerial(1); // ใช้ UART1

struct Data_Package {
  float lat;
  float lng;
  byte status;
};
Data_Package data;
const byte address[6] = "00001";

unsigned long lastSendTime = 0;

void setup() {
  Serial.begin(115200);

  // 1. ตั้งค่า SPI ให้หนีขา 23 (เพราะเอาไปใช้กับ GPS แล้ว)
  // SPI.begin(SCK, MISO, MOSI, SS);
  SPI.begin(18, 19, 27, 5); // ⚠️ ให้ NRF24 ใช้ MOSI ขา 27 แทน

  // 2. ตั้งค่า GPS ให้ใช้ขา 23, 22
  // gpsSerial.begin(Baud, Config, RX_Pin, TX_Pin);
  gpsSerial.begin(9600, SERIAL_8N1, GPS_RX_PIN, GPS_TX_PIN);

  if (!radio.begin()) {
    Serial.println("❌ NRF24 Hardware Error! Check wiring on Pin 27/18/19");
    while (1);
  }

  radio.openWritingPipe(address);
  radio.setPALevel(RF24_PA_MAX);
  radio.setDataRate(RF24_250KBPS); // ต้องตรงกับตัวรับ
  radio.stopListening();
  
  Serial.println("✅ Sender Ready!");
  Serial.print("   GPS RX on Pin: "); Serial.println(GPS_RX_PIN);
  Serial.print("   NRF MOSI moved to Pin: 27");
}

void loop() {
  // อ่านค่า GPS
  while (gpsSerial.available() > 0) {
    if (gps.encode(gpsSerial.read())) {
      if (gps.location.isValid()) {
        data.lat = gps.location.lat();
        data.lng = gps.location.lng();
        data.status = 1;
      } else {
        data.status = 0;
      }
    }
  }

  // ส่งข้อมูลทุก 1 วินาที
  if (millis() - lastSendTime > 1000) {
    
    // --- โหมดเทส (ถ้ายังไม่ออกไปตากแดด ให้เปิดบรรทัดนี้เพื่อเช็คระบบก่อน) ---
    // data.lat = 13.7563; data.lng = 100.5018; data.status = 1; 
    
    Serial.print("Sending... ");
    bool report = radio.write(&data, sizeof(Data_Package));
    
    if (report) {
      Serial.print("✅ OK! Lat: "); Serial.print(data.lat, 6);
      Serial.println(" (Sent)");
    } else {
      Serial.println("❌ Failed (Check Receiver)");
    }
    
    lastSendTime = millis();
  }
}