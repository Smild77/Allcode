import customtkinter as ctk
import threading
import time
from pymodbus.client import ModbusSerialClient

# --- ตั้งค่า Theme ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class PLCControlApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("PLC Control Interface (Modbus RTU)")
        self.geometry("1100x700") 
        
        # ตัวแปรสำหรับ Modbus Client
        self.client = None
        self.is_connected = False
        self.monitoring = False # เอาไว้คุม Thread

        # ================= [1] ส่วนบน: การเชื่อมต่อ =================
        self.frame_top = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_top.pack(side="top", fill="x", padx=20, pady=10)

        ctk.CTkLabel(self.frame_top, text="Comport:", font=("Arial", 14, "bold")).pack(side="left", padx=(0, 5))
        # *เลือก COM Port*
        self.combo_port = ctk.CTkComboBox(self.frame_top, values=["COM3", "COM4", "COM5", "COM6"], width=100)
        self.combo_port.pack(side="left", padx=5)

        self.btn_connect = ctk.CTkButton(self.frame_top, text="Connect", width=100, fg_color="#333333", border_width=1, border_color="white", command=self.toggle_connection)
        self.btn_connect.pack(side="left", padx=20)

        ctk.CTkLabel(self.frame_top, text="Status:", font=("Arial", 14, "bold")).pack(side="left", padx=5)
        self.lbl_status_conn = ctk.CTkLabel(self.frame_top, text="Disconnected", text_color="red")
        self.lbl_status_conn.pack(side="left")

        # ================= [2] Monitor Log =================
        self.frame_monitor = ctk.CTkFrame(self, fg_color="#1a1a1a", border_width=2, border_color="#333")
        self.frame_monitor.pack(side="top", fill="x", padx=20, pady=5)
        
        ctk.CTkLabel(self.frame_monitor, text="SYSTEM MONITOR / LOG", font=("Arial", 14, "bold"), text_color="#00AAFF").pack(anchor="w", padx=10, pady=(5,0))
        self.txt_status_log = ctk.CTkTextbox(self.frame_monitor, font=("Consolas", 18), height=150, text_color="#00FF00")
        self.txt_status_log.pack(fill="both", expand=True, padx=10, pady=10)

        # ================= [3] Controls & Sensors =================
        self.frame_middle = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_middle.pack(side="top", fill="both", expand=True, padx=20, pady=10)

        self.frame_controls = ctk.CTkFrame(self.frame_middle, fg_color="transparent")
        self.frame_controls.pack(side="left", fill="both", expand=True)

        self.grid_motors = ctk.CTkFrame(self.frame_controls, fg_color="transparent")
        self.grid_motors.pack(fill="both", expand=True)
        self.grid_motors.grid_columnconfigure((0,1,2), weight=1)

        # สร้างแผง M1, M2, M3
        self.create_m1_panel(self.grid_motors, 0)
        self.create_m2_panel(self.grid_motors, 1)
        self.create_m3_panel(self.grid_motors, 2)

        # --- แผง Sensor ขวา ---
        self.frame_sensors = ctk.CTkFrame(self.frame_middle, width=200, fg_color="#222222")
        self.frame_sensors.pack(side="right", fill="y", padx=(10, 0))
        ctk.CTkLabel(self.frame_sensors, text="SENSORS", font=("Arial", 16, "bold"), text_color="white").pack(pady=15)
        
        # ตาราง Limit Switch
        self.frame_limits_grid = ctk.CTkFrame(self.frame_sensors, fg_color="transparent")
        self.frame_limits_grid.pack(fill="x", padx=10)

        # X12, X14 (แถวบน)
        self.lamp_limit1 = self.create_lamp_cell(self.frame_limits_grid, "L (X12)", 0, 0)
        self.lamp_limit3 = self.create_lamp_cell(self.frame_limits_grid, "X14", 0, 1)

        # X13, X15 (แถวล่าง)
        self.lamp_limit2 = self.create_lamp_cell(self.frame_limits_grid, "R (X13)", 1, 0)
        self.lamp_limit4 = self.create_lamp_cell(self.frame_limits_grid, "X15", 1, 1)
        
        # เส้นขีดคั่น
        ctk.CTkFrame(self.frame_sensors, height=2, fg_color="gray").pack(fill="x", pady=10, padx=20)
        
        # --- กลุ่ม Prox/Safety (แก้ไขชื่อเป็น X4, X5 แล้วครับ) ---
        self.lamp_prox1 = self.create_indicator(self.frame_sensors, "Left (X4)")
        self.lamp_prox2 = self.create_indicator(self.frame_sensors, "Right (X5)")

        # ================= [4] Bottom Buttons =================
        self.frame_bottom = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_bottom.pack(side="bottom", fill="x", padx=20, pady=20)

        self.btn_home = ctk.CTkButton(self.frame_bottom, text="HOME ALL", width=140, height=50, fg_color="#555555", font=("Arial", 16), command=lambda: self.write_coil(50, True)) 
        self.btn_home.pack(side="left", padx=10)

        self.btn_start = ctk.CTkButton(self.frame_bottom, text="START AUTO", height=60, font=("Arial", 22, "bold"), fg_color="#00AA00", command=lambda: self.write_coil(66, True))
        self.btn_start.pack(side="left", fill="x", expand=True, padx=20)

        self.btn_stop = ctk.CTkButton(self.frame_bottom, text="STOP", width=140, height=50, fg_color="#CC0000", hover_color="#990000", command=lambda: self.write_coil(0, True)) # M0 Stop
        self.btn_stop.pack(side="right", padx=10)

    # ================= [ส่วนเชื่อมต่อ Modbus] หัวใจสำคัญ =================
    
    def toggle_connection(self):
        if not self.is_connected:
            port = self.combo_port.get()
            try:
                self.log_cmd(f"Connecting to {port}...")
                self.client = ModbusSerialClient(
                    port=port, baudrate=9600, bytesize=8, parity='N', stopbits=1, timeout=0.5
                )
                
                if self.client.connect():
                    self.is_connected = True
                    self.btn_connect.configure(text="Disconnect", fg_color="green")
                    self.lbl_status_conn.configure(text="Connected", text_color="green")
                    self.log_cmd("PLC Connected! Starting Monitor...")
                    
                    self.monitoring = True
                    threading.Thread(target=self.monitor_loop, daemon=True).start()
                else:
                    self.log_cmd("Connection Failed! Check cable/port.")
            except Exception as e:
                self.log_cmd(f"Error: {e}")
        else:
            self.monitoring = False
            self.client.close()
            self.is_connected = False
            self.btn_connect.configure(text="Connect", fg_color="#333333")
            self.lbl_status_conn.configure(text="Disconnected", text_color="red")
            self.log_cmd("Disconnected.")

    def monitor_loop(self):
        """ อ่านค่าจาก PLC ตลอดเวลา (Background Thread) """
        while self.monitoring:
            try:
                if self.client.connect():
                    # อ่าน Input X0 - X23
                    rr = self.client.read_discrete_inputs(0, 24, slave=1) 
                    
                    if not rr.isError():
                        bits = rr.bits
                        if len(bits) >= 16: # เช็คให้แน่ใจว่าอ่านมาครบ
                            # Limit Switches
                            self.update_lamp(self.lamp_limit1, bits[12]) # X12
                            self.update_lamp(self.lamp_limit2, bits[13]) # X13
                            self.update_lamp(self.lamp_limit3, bits[14]) # X14
                            self.update_lamp(self.lamp_limit4, bits[15]) # X15
                            
                            # *** แก้ไขตรงนี้เป็น X4 และ X5 ***
                            self.update_lamp(self.lamp_prox1, bits[4]) # Left (X4)
                            self.update_lamp(self.lamp_prox2, bits[5]) # Right (X5)
            except Exception as e:
                print(f"Monitor Error: {e}")
            
            time.sleep(0.1)

    def write_coil(self, address, value):
        if self.is_connected:
            self.client.write_coil(address, True, slave=1)
            time.sleep(0.1)
            self.client.write_coil(address, False, slave=1)
            self.log_cmd(f"Write M{address} -> ON")
        else:
            self.log_cmd(f"Offline: M{address} (Simulated)")

    # ================= UI Helpers =================
    
    def create_lamp_cell(self, parent, text, r, c):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.grid(row=r, column=c, padx=5, pady=5, sticky="w")
        lamp = ctk.CTkLabel(frame, text="●", font=("Arial", 24), text_color="#444444")
        lamp.pack(side="left")
        ctk.CTkLabel(frame, text=text, font=("Arial", 12)).pack(side="left")
        return lamp

    def create_m1_panel(self, parent, col):
        frame = ctk.CTkFrame(parent, border_width=2, border_color="#D35400")
        frame.grid(row=0, column=col, padx=5, pady=5, sticky="nsew")
        ctk.CTkLabel(frame, text="M1: LOCKING", font=("Arial", 16, "bold"), text_color="#D35400").pack(pady=5)
        ctk.CTkButton(frame, text="LOCK", fg_color="#D35400", command=lambda: self.write_coil(1, True)).pack(fill="x", padx=10, pady=10)
        ctk.CTkButton(frame, text="UNLOCK", fg_color="#E59866", command=lambda: self.write_coil(10, True)).pack(fill="x", padx=10, pady=5)

    def create_m2_panel(self, parent, col):
        frame = ctk.CTkFrame(parent, border_width=2, border_color="#2E86C1")
        frame.grid(row=0, column=col, padx=5, pady=5, sticky="nsew")
        ctk.CTkLabel(frame, text="M2: PISTON", font=("Arial", 16, "bold"), text_color="#2E86C1").pack(pady=5)
        ctk.CTkButton(frame, text="PUSH", fg_color="#2E86C1", command=lambda: self.write_coil(2, True)).pack(fill="x", padx=10, pady=10)
        ctk.CTkButton(frame, text="PULL", fg_color="#85C1E9", command=lambda: self.write_coil(20, True)).pack(fill="x", padx=10, pady=5)

    def create_m3_panel(self, parent, col):
        frame = ctk.CTkFrame(parent, border_width=2, border_color="#27AE60")
        frame.grid(row=0, column=col, padx=5, pady=5, sticky="nsew")
        ctk.CTkLabel(frame, text="M3: SLIDE", font=("Arial", 16, "bold"), text_color="#27AE60").pack(pady=5)
        ctk.CTkButton(frame, text="< LEFT", fg_color="#27AE60", width=60, command=lambda: self.write_coil(3, True)).pack(side="left", padx=10, pady=20)
        ctk.CTkButton(frame, text="RIGHT >", fg_color="#27AE60", width=60, command=lambda: self.write_coil(30, True)).pack(side="right", padx=10, pady=20)

    def create_indicator(self, parent, label_text):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(pady=5, anchor="w", padx=10)
        lamp = ctk.CTkLabel(frame, text="●", font=("Arial", 24), text_color="#444444")
        lamp.pack(side="left", padx=(0, 5))
        ctk.CTkLabel(frame, text=label_text, font=("Arial", 12)).pack(side="left")
        return lamp

    def update_lamp(self, lamp_widget, status):
        color = "#FF0000" if status else "#444444"
        lamp_widget.configure(text_color=color)

    def log_cmd(self, msg):
        self.txt_status_log.insert("end", f"\n{msg}")
        self.txt_status_log.see("end")

if __name__ == "__main__":
    app = PLCControlApp()
    app.mainloop()