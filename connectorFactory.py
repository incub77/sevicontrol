from connectorRS485 import ConnectorRS485
from connectorDummy import ConnectorDummy

def ConnectorFactory(device, baudrate=None):
    if device == "dummy":
        return ConnectorDummy()
    else:
        return ConnectorRS485(device, baudrate)