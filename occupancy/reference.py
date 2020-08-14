# packages
import sys
import numpy  as np
import pandas as pd

# project
from occupancy import helpers

class Reference():
    """
    One Reference class project.
    Keeps track of all reference sensors in project.
    When event_data json is received, calculate latest reference value as
    the average of all reference sensors.

    """

    def __init__(self, args):
        # add to self
        self.args = args

        # initial values
        self.devices      = {}
        self.n_devices    = 0
        self.latest_value = 0

        # initialise lists and dictionaries
        self.timestamp   = []
        self.unixtime    = []
        self.temperature = []
        self.latest_values = {}


    def add_device(self, device, device_id):
        """
        Add new device from which the reference value is sourced.

        Parameters
        ----------
        device : dictionary
            Device information json in dictionary format.
        device_id : str
            Device identifier.

        """

        # add new device to self
        self.devices[device_id] = device
        self.n_devices += 1

        # add temperature lists to device
        self.devices[device_id]['timestamp']   = []
        self.devices[device_id]['unixtime']    = []
        self.devices[device_id]['temperature'] = []
        self.latest_values[device_id] = None


    def new_event_data(self, event_data, device_id):
        """
        Receive new event data json from Director and update reference value.

        Parameters
        ----------
        event_data : dictionary
            Data json containing new event data.
        device_id : str
            Identifier of source device.

        """

        # isolate timestamp and temperature value
        temperature = event_data['data']['temperature']['value']
        timestamp, unixtime = helpers.convert_event_data_timestamp(event_data['timestamp'])

        # append to lists
        self.devices[device_id]['timestamp'].append(timestamp)
        self.devices[device_id]['unixtime'].append(unixtime)
        self.devices[device_id]['temperature'].append(temperature)

        # update latest value
        self.latest_values[device_id] = temperature

        # append time lists
        self.timestamp.append(timestamp)
        self.unixtime.append(unixtime)

        # calculate reference as mean of all references
        meanval = 0
        n = 0
        for device_id in self.latest_values.keys():
            if self.latest_values[device_id] is not None:
                meanval += self.latest_values[device_id]
                n += 1
        if n > 0:
            meanval /= n

        # average temperature with last value if less than 10 minutes ago
        if len(self.temperature) > 0 and self.unixtime[-1] - self.unixtime[-2] < 60*10:
            self.latest_value = (self.temperature[-1]+meanval)/2
        else:
            self.latest_value = meanval
        
        # append lists
        self.temperature.append(self.latest_value)

