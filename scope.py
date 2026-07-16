import pyvisa
import tkinter as tk
from PIL import Image, ImageTk
from tkinter import scrolledtext

class ScopeController:
    """Simple SCPI controller for a USB oscilloscope."""
    def __init__(self, backend="@py", timeout=2000):
        self.backend = backend
        self.timeout = timeout
        self.rm = None
        self.scope = None
        self.photo = None
        self.is_streaming = False
        self.log_callback = None

    def connect(self):
        """Connect to the first USB instrument."""
        self.rm = pyvisa.ResourceManager(self.backend)
        print(self.rm.list_resources())
        for resource in self.rm.list_resources():
            if resource.startswith("USB"):
                self.scope = self.rm.open_resource(resource)
                self.scope.timeout = self.timeout
                print(f"Connected to: {resource}")
                return
        raise RuntimeError("No USB instrument found.")

    def disconnect(self):
        """Close the instrument and VISA resource manager."""
        if self.scope is not None:
            self.scope.close()
        self.scope = None
        if self.rm is not None:
            self.rm.close()
        self.rm = None

    def write(self, command):
        """Send a SCPI command."""
        self.log(f">> {command}")
        self.scope.write(command)

    def query(self, command, timeout=None):
        """Send a SCPI query and return the response."""
        if timeout is not None:
            self.scope.timeout = timeout

        self.log(f">> {command}")

        response = self.scope.query(command).strip()

        self.log(f"<< {response}")

        return response

    def get_idn(self):
        """Return the instrument identification string."""
        return self.query("*IDN?")

    def run(self):
        """Start waveform acquisition."""
        self.write(":RUN")

    def stop(self):
        """Stop waveform acquisition."""
        self.write(":STOP")

    def read_ieee_block(self, scope):
        """
        Read an IEEE-488.2 definite-length binary block.
        """
        header = scope.read_bytes(2)

        if header[0:1] != b"#":
            raise RuntimeError(
                f"Unexpected header {header!r}"
            )

        digits = int(header[1:2])

        if digits == 0:
            raise RuntimeError(
                "Indefinite-length block not supported."
            )

        length = int(scope.read_bytes(digits).decode())

        data = scope.read_bytes(length)

        return data

    def capture_temp(self):
        self.scope.timeout = 5000

        self.write(":DISPlay:SNAP?")

        data = self.read_ieee_block(self.scope)

        filename = "scope.png"

        # ลบไฟล์เก่าก่อน
        try:
            open(filename, "rb").close()
            import os
            os.remove(filename)
        except:
            pass

        with open(filename, "wb") as f:
            f.write(data)

        return filename

    def log(self, text):
        if self.log_callback:
            self.log_callback(text)

    def Voltage_Div_200mV(self, channel):
        """Set the voltage division setting for a specific channel to 200 mV."""
        self.write(f":CHANnel{channel}:SCALe 0.2")

    def Voltage_Div_500mV(self, channel):
        """Set the voltage division setting for a specific channel to 500 mV."""
        self.write(f":CHANnel{channel}:SCALe 0.5")

    def Voltage_Div_1V(self, channel):
        """Set the voltage division setting for a specific channel to 1 V."""
        self.write(f":CHANnel{channel}:SCALe 1")

    def Voltage_Div_2V(self, channel):
        """Set the voltage division setting for a specific channel to 2 V."""
        self.write(f":CHANnel{channel}:SCALe 2")

    def Voltage_Div_5V(self, channel):
        """Set the voltage division setting for a specific channel to 5 V."""
        self.write(f":CHANnel{channel}:SCALe 5")

    def Time_Div_10ms(self):
        """Set the time division setting to 10 ms."""
        self.write(":TIMebase:SCALe 1e-2")

    def Time_Div_1ms(self):
        """Set the time division setting to 1 ms."""
        self.write(":TIMebase:SCALe 1e-3")

    def Time_Div_100us(self):
        """Set the time division setting to 100 us."""
        self.write(":TIMebase:SCALe 1e-4")

    def Time_Div_10us(self):
        """Set the time division setting to 10 us."""
        self.write(":TIMebase:SCALe 1e-5")

    def Time_Div_1us(self):
        """Set the time division setting to 1 us."""
        self.write(":TIMebase:SCALe 1e-6")

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()

class ScopeGUI:
    def __init__(self):
        self.scope = ScopeController()

        self.root = tk.Tk()
        self.root.title("RIGOL Oscilloscope Controller")
        self.root.geometry("1350x725")
        self.root.protocol(
            "WM_DELETE_WINDOW",
            self.close
        )       

        self.create_widgets()

        self.scope.log_callback = self.add_log

    def close(self):
        self.is_streaming = False
        try:
            self.scope.disconnect()
        except:
            pass

        self.root.destroy()

    def connect(self):
        try:
            self.scope.connect()
            self.status.config(text="Status : Connected", fg="green")
            print(self.scope.get_idn())
            self.is_streaming = True
            self.update_live()
        except Exception as e:
            self.status.config(text=str(e), fg="red")
    
    def disconnect(self):
        self.scope.disconnect()

        self.status.config(
            text="Status : Disconnected",
            fg="red"
        )

    def update_live(self): #นำภาพจาก scope มาแสดงใน GUI
        if not self.is_streaming:
            return
        try:
            filename = self.scope.capture_temp()

            img = Image.open(filename)
            img = img.resize((650,400))

            self.photo = ImageTk.PhotoImage(img)

            self.image_label.config(image=self.photo, text="")
            self.image_label.image = self.photo

        except Exception as e:
            print(e)

        self.root.after(1000, self.update_live)

    def start(self): 
        try:
            if self.scope.scope is None:
                self.status.config(text="Please Connect First", fg="red")
                return
            else:
                self.scope.run()

        except Exception as e:
            self.status.config(text=str(e), fg="red")

    def stop(self):
        try:
            if self.scope.scope is None:
                self.status.config(text="Please Connect First", fg="red")
                return
            else:
                self.scope.stop()

        except Exception as e:
            self.status.config(text=str(e), fg="red")

    def send_scpi(self): #ส่งคำสั่ง SCPI ไปยัง scope และแสดงผลลัพธ์ใน log
        cmd = self.scpi_entry.get().strip()

        if cmd.endswith("?"):
            response = self.scope.query(cmd)
            print(response)
        else:
            self.scope.write(cmd)

    def create_widgets(self): #กำหนด layout ของ GUI
        """สร้าง status frame, control panel, channel controls, time division controls, SCPI log, and oscilloscope screen."""
        self.status_frame = tk.LabelFrame(self.root,text="Status")
        self.status_frame.grid(row=0, column=2, padx=10, pady=0, sticky="ew")

        self.status = tk.Label(
            self.status_frame,
            text="Status : Disconnected",
            fg="red"
        )
        self.status.pack()

        self.button_frame = tk.Frame(self.status_frame)
        self.button_frame.pack()

        self.channel_container = tk.Frame(self.root)
        self.channel_container.grid(row=7, column=0,
                                    columnspan=4,
                                    sticky="ew",
                                    padx=10)

        for i in range(4):
            self.channel_container.grid_columnconfigure(i, weight=1, uniform="channel")

        self.control_frame = tk.LabelFrame(
            self.root,
            text="Control Panel"
        )
        self.control_frame.grid(row=1, column=2, padx=10, pady=10, sticky="ew")

        self.channel1_frame = tk.LabelFrame(self.channel_container,
                                            text="Channel 1 Control")
        self.channel1_frame.grid(row=0, column=0, padx=5, sticky="ew")

        self.voltage1_frame = tk.LabelFrame(self.channel1_frame, text="Voltage")
        self.voltage1_frame.grid(row=1, column=0, padx=5, pady=5, sticky="ew")

        self.channel2_frame = tk.LabelFrame(self.channel_container,
                                            text="Channel 2 Control")
        self.channel2_frame.grid(row=0, column=1, padx=5, sticky="ew")

        self.voltage2_frame = tk.LabelFrame(self.channel2_frame, text="Voltage")
        self.voltage2_frame.grid(row=1, column=0, padx=5, pady=5, sticky="ew")

        self.channel3_frame = tk.LabelFrame(self.channel_container,
                                            text="Channel 3 Control")
        self.channel3_frame.grid(row=0, column=2, padx=5, sticky="ew")

        self.voltage3_frame = tk.LabelFrame(self.channel3_frame, text="Voltage")
        self.voltage3_frame.grid(row=1, column=0, padx=5, pady=5, sticky="ew")

        self.channel4_frame = tk.LabelFrame(self.channel_container,
                                            text="Channel 4 Control")
        self.channel4_frame.grid(row=0, column=3, padx=5, sticky="ew")
       
        self.voltage4_frame = tk.LabelFrame(self.channel4_frame, text="Voltage")
        self.voltage4_frame.grid(row=1, column=0, padx=5, pady=5, sticky="ew")

        self.time_frame = tk.LabelFrame(
            self.root,
            text="Time Division Control"
        )
        self.time_frame.grid(row=5, column=2, padx=10, pady=10, sticky="ew")

        tk.Label(self.root, text="Enter a SCPI command:").grid(row=2, column=2, sticky="w", padx=10, pady=5)

        self.scpi_entry = tk.Entry(self.root, width=50)
        self.scpi_entry.grid(row=3, column=2, padx=10, pady=5)

        tk.Button(self.root, text="Send", command=self.send_scpi).grid(row=4, column=2, pady=5)

        tk.Button(
            self.button_frame,
            text="Connect",
            command=self.connect
        ).grid(row=0,column=0)

        tk.Button(
            self.button_frame,
            text="Disconnect",
            command=self.disconnect
        ).grid(row=0,column=1,padx=5)

        tk.Button(
            self.control_frame,
            text="START",
            command=self.start
        ).grid(row=1,column=0,padx=5)

        tk.Button(
            self.control_frame,
            text="STOP",
            command=self.stop
        ).grid(row=1,column=1,padx=5)

        tk.Button(
            self.control_frame,
            text="Capture",
            command=self.capture_screen
        ).grid(row=1, column=2, padx=5)

        tk.Button(
            self.voltage1_frame,
            text="200 mV",
            command=lambda: self.scope.Voltage_Div_200mV(1)
        ).grid(row=0, column=0, padx=5, pady=5)

        tk.Button(
            self.voltage1_frame,
            text="500 mV",
            command=lambda: self.scope.Voltage_Div_500mV(1)
        ).grid(row=0, column=1, padx=5, pady=5)

        tk.Button(
            self.voltage1_frame,
            text="1 V",
            command=lambda: self.scope.Voltage_Div_1V(1)
        ).grid(row=0, column=2, padx=5, pady=5)

        tk.Button(
            self.voltage1_frame,
            text="2 V",
            command=lambda: self.scope.Voltage_Div_2V(1)
        ).grid(row=0, column=3, padx=5, pady=5)

        tk.Button(
            self.voltage1_frame,
            text="5 V",
            command=lambda: self.scope.Voltage_Div_5V(1)
        ).grid(row=0, column=4, padx=5, pady=5)

        tk.Button(
            self.voltage2_frame,
            text="200 mV",
            command=lambda: self.scope.Voltage_Div_200mV(2)
        ).grid(row=0, column=0, padx=5, pady=5)

        tk.Button(
            self.voltage2_frame,
            text="500 mV",
            command=lambda: self.scope.Voltage_Div_500mV(2)
        ).grid(row=0, column=1, padx=5, pady=5)

        tk.Button(
            self.voltage2_frame,
            text="1 V",
            command=lambda: self.scope.Voltage_Div_1V(2)
        ).grid(row=0, column=2, padx=5, pady=5)

        tk.Button(
            self.voltage2_frame,
            text="2 V",
            command=lambda: self.scope.Voltage_Div_2V(2)
        ).grid(row=0, column=3, padx=5, pady=5)

        tk.Button(
            self.voltage2_frame,
            text="5 V",
            command=lambda: self.scope.Voltage_Div_5V(2)
        ).grid(row=0, column=4, padx=5, pady=5)

        tk.Button(
            self.voltage3_frame,
            text="200 mV",
            command=lambda: self.scope.Voltage_Div_200mV(3)
        ).grid(row=0, column=0, padx=5, pady=5)

        tk.Button(
            self.voltage3_frame,
            text="500 mV",
            command=lambda: self.scope.Voltage_Div_500mV(3)
        ).grid(row=0, column=1, padx=5, pady=5)

        tk.Button(
            self.voltage3_frame,
            text="1 V",
            command=lambda: self.scope.Voltage_Div_1V(3)
        ).grid(row=0, column=2, padx=5, pady=5)

        tk.Button(
            self.voltage3_frame,
            text="2 V",
            command=lambda: self.scope.Voltage_Div_2V(3)
        ).grid(row=0, column=3, padx=5, pady=5)

        tk.Button(
            self.voltage3_frame,
            text="5 V",
            command=lambda: self.scope.Voltage_Div_5V(3)
        ).grid(row=0, column=4, padx=5, pady=5)

        tk.Button(
            self.voltage4_frame,
            text="200 mV",
            command=lambda: self.scope.Voltage_Div_200mV(4)
        ).grid(row=0, column=0, padx=5, pady=5)

        tk.Button(
            self.voltage4_frame,
            text="500 mV",
            command=lambda: self.scope.Voltage_Div_500mV(4)
        ).grid(row=0, column=1, padx=5, pady=5)

        tk.Button(
            self.voltage4_frame,
            text="1 V",
            command=lambda: self.scope.Voltage_Div_1V(4)
        ).grid(row=0, column=2, padx=5, pady=5)

        tk.Button(
            self.voltage4_frame,
            text="2 V",
            command=lambda: self.scope.Voltage_Div_2V(4)
        ).grid(row=0, column=3, padx=5, pady=5)

        tk.Button(
            self.voltage4_frame,
            text="5 V",
            command=lambda: self.scope.Voltage_Div_5V(4)
        ).grid(row=0, column=4, padx=5, pady=5)

        tk.Button(
            self.time_frame,
            text="10 ms",
            command=self.scope.Time_Div_10ms
        ).grid(row=0, column=0, padx=5, pady=5)

        tk.Button(
            self.time_frame,
            text="100 us",
            command=self.scope.Time_Div_100us
        ).grid(row=0, column=2, padx=5, pady=5)

        tk.Button(
            self.time_frame,
            text="10 us",
            command=self.scope.Time_Div_10us
        ).grid(row=0, column=3, padx=5, pady=5)

        tk.Button(
            self.time_frame,
            text="1 us",
            command=self.scope.Time_Div_1us
        ).grid(row=0, column=4, padx=5, pady=5)

        tk.Button(
            self.time_frame,
            text="1 ms",
            command=self.scope.Time_Div_1ms
        ).grid(row=0, column=1, padx=5, pady=5)

        self.log_frame = tk.LabelFrame(
            self.root,
            text="SCPI Log"
        )
        self.log_frame.grid(
            row=8,
            column=0,
            columnspan=4,
            padx=10,
            pady=10,
            sticky="nsew"
        )
        self.log_text = scrolledtext.ScrolledText(
            self.log_frame,
            height=8
        )
        self.log_text.pack(fill="both", expand=True)
        self.log_text.config(state="disabled")

        self.image_frame = tk.LabelFrame(
            self.root,
            text="Oscilloscope Screen",
            width=670,
            height=420
        )

        self.image_frame.grid(
            row=0,
            column=0,
            rowspan=6,
            padx=10,
            pady=10,
            sticky="nw"
        )

        self.image_frame.grid_propagate(False)

        self.image_label = tk.Label(self.image_frame, text="No Image")
        self.image_label.place(relx=0.5, rely=0.5, anchor="center")

        self.root.grid_columnconfigure(0, weight=0)
        self.root.grid_columnconfigure(1, minsize=20)   # ช่องว่าง
        self.root.grid_columnconfigure(2, weight=1)
        self.root.grid_columnconfigure(3, weight=1)

        self.channel_var1 = tk.IntVar()
        self.channel_var2 = tk.IntVar()
        self.channel_var3 = tk.IntVar()
        self.channel_var4 = tk.IntVar()
        self.checkbox1 = tk.Checkbutton(
            self.channel1_frame,
            text="Channel 1 : OFF",
            variable=self.channel_var1,
            command=lambda: self.channel_select(1)
        )

        self.checkbox1.grid(
            row=2,
            column=0,
            columnspan=5,
            sticky="w",
            padx=5,
            pady=(5,0)
        )

        self.checkbox2 = tk.Checkbutton(
            self.channel2_frame,
            text="Channel 2 : OFF",
            variable=self.channel_var2,
            command=lambda: self.channel_select(2)
        )

        self.checkbox2.grid(
            row=2,
            column=0,
            columnspan=5,
            sticky="w",
            padx=5,
            pady=(5,0)
        )

        self.checkbox3 = tk.Checkbutton(
            self.channel3_frame,
            text="Channel 3 : OFF",
            variable=self.channel_var3,
            command=lambda: self.channel_select(3)
        )

        self.checkbox3.grid(
            row=2,
            column=0,
            columnspan=5,
            sticky="w",
            padx=5,
            pady=(5,0)
        )

        self.checkbox4 = tk.Checkbutton(
            self.channel4_frame,
            text="Channel 4 : OFF",
            variable=self.channel_var4,
            command=lambda: self.channel_select(4)
        )

        self.checkbox4.grid(
            row=2,
            column=0,
            columnspan=5,
            sticky="w",
            padx=5,
            pady=(5,0)
        )
