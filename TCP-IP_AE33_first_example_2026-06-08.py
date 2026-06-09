# %%
from io import StringIO
import re
import socket

import pandas as pd

# %%
# IP of the instrument - change it to the actual IP address of your AE33 instrument
INSTRUMENT_IP = '10.10.10.224'
# %%
# default parameters:
INSTRUMENT_PORT = 8002  # always the same
BUFFER_SIZE = 4096  # always the same
RECV_TIMEOUT = 2.0  # seconds

COLUMNS_AE33_DATA = ['SerialNumber', 'ID', 'StartTime', 'EndTime', 'SetupID', 'SetupTimestamp', 'Ref1', 'Sens11', 'Sens12', 'Ref2', 'Sens21', 'Sens22', 'Ref3', 'Sens31', 'Sens32', 'Ref4', 'Sens41', 'Sens42', 'Ref5', 'Sens51', 'Sens52', 'Ref6', 'Sens61', 'Sens62', 'Ref7', 'Sens71', 'Sens72', 'BC11', 'BC12', 'BC1', 'BC21', 'BC22', 'BC2', 'BC31', 'BC32', 'BC3', 'BC41', 'BC42', 'BC4', 'BC51', 'BC52', 'BC5', 'BC61', 'BC62', 'BC6', 'BC71', 'BC72', 'BC7', 'K1', 'K2', 'K3', 'K4', 'K5', 'K6', 'K7', 'BB', 'Pressure', 'Temp', 'Flow1', 'Flow2', 'FlowC', 'T_controller', 'T_supply', 'T_LED', 'ControllerStatus', 'LEDStatus', 'DetectorStatus', 'ValveStatus', 'Status', 'TapeAdvanceCount', 'TapeAdvanceLeft', 'CPU', 'DiskSpace', 'NumConnections']

COLUMNS_AE33_EXTERNAL_DEVICE_DATA = ['SerialNumber', 'ID', 'DataID', 'DeviceID', 'DeviceData']

COLUMNS_AE33_SETUP = ['serial', 'ID', 'SerialNumber', 'Timestamp', 'FirmwareVer', 'SoftwareVer', 'DataCenterIP', 'AutoConnect', 'InletFilter', 'Timebase', 'SG1', 'SG2', 'SG3', 'SG4', 'SG5', 'SG6', 'SG7', 'C', 'Area', 'Zeta', 'Aff', 'Abb', 'Pressure', 'Temp', 'ATNf1', 'ATNf2', 'Kmax', 'Kmin', 'Flow', 'FlowRepStd', 'PumpPresetValue', 'FlowFormulaA0', 'FlowFormulaA1', 'FlowFormulaB0', 'FlowFormulaB1', 'FlowFormulaC0', 'FlowFormulaC1', 'FlowFormulaD', 'FlowFormulaE', 'FlowFormulaF', 'TAtype', 'TAatnMax', 'TAinterval', 'TAtime', 'TapeRightFormulaK', 'TapeRightFormulaN', 'TapeLeftFormulaK', 'TapeLeftFormulaN', 'WarmUpInterval', 'AutoTestEnabled', 'AutoTestType', 'AutoTestDay', 'AutoTestTime', 'MeasureTimeStamp', 'HomeInfo', 'Display', 'About', 'DST', 'TimeZone', 'TapeAdvanceAdjust', 'ExternalID', 'BHparamID', 'TimeSync', 'DHCP', 'InstrumentIP', 'SubnetMask', 'Gateway', 'Baud', 'NTPserver']
# %%
def receive_all(sock, buffer_size=4096, timeout=2.0):
    sock.settimeout(timeout)
    chunks = []
    while True:
        try:
            chunk = sock.recv(buffer_size)
            if not chunk:
                break
            chunks.append(chunk)
        except socket.timeout:
            break
    return b''.join(chunks)

def request_dataview(ip, port, command, buffer_size=4096, timeout=2.0):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(timeout)
        s.connect((ip, port))
        s.send(command.encode())
        return receive_all(s, buffer_size=buffer_size, timeout=timeout)
# %%
### command HELLO
command_ae33 = 'HELLO\r\n'

data = request_dataview(ip=INSTRUMENT_IP,
                        port=INSTRUMENT_PORT,
                        command=command_ae33,
                        buffer_size=BUFFER_SIZE,
                        timeout=RECV_TIMEOUT)
text = data.decode(errors='replace')
print('Received', len(data), 'bytes')
print(text)
# %%
### command MAXID Data
command_ae33 = 'MAXID Data\r\n'

data = request_dataview(ip=INSTRUMENT_IP,
                        port=INSTRUMENT_PORT,
                        command=command_ae33,
                        buffer_size=BUFFER_SIZE,
                        timeout=RECV_TIMEOUT)
text = data.decode(errors='replace')
print('Received', len(data), 'bytes')
print(text)

# # parse data
max_data_id = int(re.search(r'AE33>(\d+)', text).group(1))
print()
print(max_data_id)

# %%
### command FETCH Data - collect last 5 rows from table Data
command_ae33 = f'FETCH Data {max_data_id-5} {max_data_id}\r\n'

data = request_dataview(ip=INSTRUMENT_IP,
                        port=INSTRUMENT_PORT,
                        command=command_ae33,
                        buffer_size=BUFFER_SIZE,
                        timeout=RECV_TIMEOUT)
text = data.decode(errors='replace')
print('Received', len(data), 'bytes')
print(text)

# in the end, you can parse data, for example convert it into pandas dataframe
df_ae33_data = pd.read_csv(StringIO(text.replace('AE33>', '').strip()),
                           sep='|',
                           names=COLUMNS_AE33_DATA)
print()
print(df_ae33_data)
# %%
### collect data from Setup table
command_ae33 = f'FETCH SETUP\r\n'

data = request_dataview(ip=INSTRUMENT_IP,
                        port=INSTRUMENT_PORT,
                        command=command_ae33,
                        buffer_size=BUFFER_SIZE,
                        timeout=RECV_TIMEOUT)
text = data.decode(errors='replace')
print('Received', len(data), 'bytes')
print(text)

# in the end, you can parse data, for example convert it into pandas dataframe
df_ae33_setup = pd.read_csv(StringIO(text.replace('AE33>', '').strip()),
                            sep='|',
                            names=COLUMNS_AE33_SETUP)
# drop duplicated serial column from setup data
df_ae33_setup = df_ae33_setup.drop(columns=['serial'], errors='ignore')
print()
print(df_ae33_setup)
# %%
### collect data from ExtDeviceData table - get MAXID and then fetch last 5 rows

command_ae33 = 'MAXID ExtDeviceData\r\n'
data = request_dataview(ip=INSTRUMENT_IP,
                        port=INSTRUMENT_PORT,
                        command=command_ae33,
                        buffer_size=BUFFER_SIZE,
                        timeout=RECV_TIMEOUT)
text = data.decode(errors='replace')
max_ext_device_data_id = int(re.search(r'AE33>(\d+)', text).group(1))

command_ae33 = f'FETCH ExtDeviceData {max_ext_device_data_id-5} {max_ext_device_data_id}\r\n'
data = request_dataview(ip=INSTRUMENT_IP,
                        port=INSTRUMENT_PORT,
                        command=command_ae33,
                        buffer_size=BUFFER_SIZE,
                        timeout=RECV_TIMEOUT)
text = data.decode(errors='replace')
print('Received', len(data), 'bytes')
print(text)

# in the end, you can parse data, for example convert it into pandas dataframe
df_ae33_device_data = pd.read_csv(StringIO(text.replace('AE33>', '').strip()),
                           sep='|',
                           names=COLUMNS_AE33_EXTERNAL_DEVICE_DATA)
print()
print(df_ae33_device_data)