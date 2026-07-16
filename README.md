# GUI_Oscilloscope
A GUI program for controlling RIGOL oscilloscopes (or devices supporting SCPI commands) via USB, using Python, PyVISA, and Tkinter.

## Features
- **connect/disconnect** oscilloscope from USB (VISA resource)
- **show graph from oscilloscope real time** update every 1 sec
- **capture the graph** (file .PNG)
- **control operations** START/STOP
- **setting Voltage/Div** there are 5 options : 200 mV, 500 mV, 1 V, 2 V, 5 V
- **setting Time/Div** there are 5 options : 1 us, 10 us, 100 us, 1 ms, 10 ms
- **on/off channel** ex. channel_1, channel_2, ...\
- **SCPI send** send SCPI to command oscilloscope
- **SCPIlog** show command that connect to oscilloscope
