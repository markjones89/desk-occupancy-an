# packages
import sys
import numpy             as np
import pandas            as pd
import matplotlib.pyplot as plt

# project
from occupancy                   import helpers
from occupancy.config.parameters import params

class Desk():
    """
    One Desk class for each desk sensor in project.
    It keeps track of the desk occupancy algorithm state.
    When event_data json is received, iterate algorithm one sample.

    """

    def __init__(self, device, device_id, args):
        # add to self
        self.args      = args
        self.device    = device
        self.device_id = device_id

        # initialise lists
        self.timestamp   = []   # timestamps
        self.unixtime    = []   # unixtime timestamp
        self.temperature = []   # raw temperature data
        self.diff        = []   # reference subtracted temperature
        self.roc         = []   # temperature rate of change in deg/min
        self.roc_thrs    = []   # temperature rate of change dynamic threshold
        self.state       = []   # algorithm state where 1 represents occupancy
        self.dsl_thrs    = []   # downslope threshold for detecting occupancy end

        # variables
        self.state_start_index = 0 
        self.state_flag        = False
        self.state_swapped     = False


    def __update_roc_threshold(self, prev_thrs_value, current_roc_value):
        """
        Increase and decrease ROC threshold dynamically by current ROC value.

        Parameters
        ----------
        prev_thrs_value : float
            Previous ROC threshold value.
        current_roc_value : float
            The ROC value calculated just before this function were called.

        Returns
        -------
        new_thrs_value : float
            Updated ROC threshold value.

        """
        
        # time-based increase
        new_thrs_value = min(params['roc']['thrs_maxval'], prev_thrs_value + params['roc']['thrs_posdiff'])
        new_thrs_value = max(params['roc']['thrs_minval'], new_thrs_value - current_roc_value * params['roc']['pulldown_modifier'])

        return new_thrs_value


    def __iterate_core(self):
        """
        Iterate occupancy estimation algorithm one sample ahead.
        This entails calculating rate of change (ROC), thresholds and tracking
        the current boolean state representing occupancy.

        """
        
        # get seconds since last sample
        dt = self.unixtime[-1] - self.unixtime[-2]

        # calculate rate of change in deg/min from last sample to now
        self.roc[-1] = helpers.temperature_roc_per_minute(dt, self.diff[-1] - self.diff[-2])

        # update dynamic roc threshold
        self.roc_thrs[-1] = self.__update_roc_threshold(self.roc_thrs[-2], self.roc[-1])

        # update state flag
        if not self.state_flag:
            # check wether or not roc_thrs has been passed
            if self.roc[-1] >= self.roc_thrs[-1]:
                self.state[-1] = 1
                self.state_flag = True
                self.state_start_index = len(self.state)-1

        else:
            # check wether or not temperature is below threshold
            if self.diff[-1] < self.dsl_thrs[-2]:
                self.state_flag = False
            else:
                self.state[-1] = 1
        
                # update temperature threshold
                self.dsl_thrs[-1] = np.mean(self.diff[self.state_start_index:])
        
        # reset state swapped
        self.state_swapped = False


    def new_event_data(self, event_data, latest_reference):
        """
        Receive new event data json from Director and iterate estimation algorithm one step.

        Parameters
        ----------
        event_data : dictionary
            Event data json in dictionary form containing new event data.
        latest_reference : float
            The most recent reference temperature value.
            Is 0 if no reference is yet found.

        """

        # isolate timestamp and temperature value
        temperature = event_data['data']['temperature']['value']
        timestamp, unixtime = helpers.convert_event_data_timestamp(event_data['timestamp'])

        # check for duplicate event
        if len(self.unixtime) > 0 and unixtime - self.unixtime[-1] == 0:
            return

        # append time lists
        self.timestamp.append(timestamp)
        self.unixtime.append(unixtime)

        # average temperature with last value if less than 10 minutes ago
        if len(self.temperature) > 0 and self.unixtime[-1] - self.unixtime[-2] < 60*10:
            self.temperature.append((self.temperature[-1]+temperature)/2)
        else:
            self.temperature.append(temperature)

        # append one default value to supporting lists
        self.diff.append(self.temperature[-1] - latest_reference)
        self.roc.append(0)
        self.roc_thrs.append(params['roc']['thrs_maxval'])
        self.dsl_thrs.append(np.nan)
        self.state.append(0)

        # stop here if this is first call
        if len(self.timestamp) < 2:
            return

        # iterate algorithm for last sample
        self.__iterate_core()

