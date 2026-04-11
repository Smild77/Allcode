import serial
import time

SERIAL_PORT = "COM8"
BAUD_RATE = 9600

def send_command(ser, command_str, description):
    # ส่งคำสั่งไปที่บอร์ด
    ser.write(command_str.encode('utf-8'))
    print(f"ส่งคำสั่ง: {description}")
    
    # รออ่านข้อความยืนยันที่บอร์ดพิมพ์ตอบกลับมา (ถ้ามี)
    response = ser.readline().decode('utf-8').strip()
    if response:
        print(f"-> บอร์ดตอบกลับ: {response}")
    print("-" * 30)

try:
    # ตั้ง timeout ให้รออ่านค่าสัก 1 วินาที
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    time.sleep(2) # รอไมโครคอนโทรลเลอร์รีเซ็ต
    print("เชื่อมต่อ COM8 สำเร็จ! เริ่มรันซีเควนซ์...\n")

    send_command(ser, "m1\n", "m1 (Motor 1 started)")
    time.sleep(3)
    
    send_command(ser, "m2\n", "m2 (Motor 2 started)")
    time.sleep(3)
    
    send_command(ser, "m1s\nm2s\n", "stop all (All motors stopped)")

except serial.SerialException as e:
    print(f"เกิดข้อผิดพลาด: {e} (เช็คสายเสียบ หรือดูว่ามีโปรแกรมอื่นแย่งใช้ COM8 อยู่ไหม)")
finally:
    # ปิดพอร์ตเสมอไม่ว่าจะเกิด Error หรือไม่
    if 'ser' in locals() and ser.is_open:
        ser.close()
        print("ปิดการเชื่อมต่อเรียบร้อย")