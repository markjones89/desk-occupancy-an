# packages
import os
import sys
import json
import time
import pprint
import requests
import argparse
import datetime
import sseclient
import numpy             as np
import pandas            as pd
import matplotlib.pyplot as plt

# project
import occupancy.helpers         as hlp
import occupancy.config.styling  as stl
from occupancy.desk              import Desk
from occupancy.reference         import Reference
from occupancy.config.parameters import params


class Director():
    """
    Keeps track of all sensors in project and separates desks from references.
    Spawns one Desk object per desk sensors and one Reference object.
    When new event_data json is received, relay it to the correct desk- or reference object.

    """

    def __init__(self, username, password, project_id, api_url_base):
        # give to self
        self.username     = username
        self.password     = password
        self.project_id   = project_id
        self.api_url_base = api_url_base

        # occupancy lists
        self.hourly_occupancy_timestamp  = []
        self.hourly_occupancy_percentage = []
        self.daily_occupancy_timestamp   = []
        self.daily_occupancy_percentage  = []

        # set stream endpoint
        self.stream_endpoint = "{}/projects/{}/devices:stream".format(self.api_url_base, self.project_id)

        # parse system arguments
        self.__parse_sysargs()

        # set filters for fetching data
        self.__set_filters()

        # fetch list of devices in project
        self.__fetch_project_devices()

        # spawn devices instances
        self.__spawn_devices()


    def __parse_sysargs(self):
        """
        Parse for command line arguments.

        """

        # create parser object
        parser = argparse.ArgumentParser(description='Desk Occupancy Estimation on Stream and Event History.')

        # get UTC time now
        now = (datetime.datetime.utcnow().replace(microsecond=0)).isoformat() + 'Z'

        # general arguments
        parser.add_argument('--starttime', metavar='', help='Event history UTC starttime [YYYY-MM-DDTHH:MM:SSZ].', required=False, default=now)
        parser.add_argument('--endtime',   metavar='', help='Event history UTC endtime [YYYY-MM-DDTHH:MM:SSZ].',   required=False, default=now)

        # boolean flags
        parser.add_argument('--plot',   action='store_true', help='Plot the estimated desk occupancy.')
        parser.add_argument('--debug',  action='store_true', help='Visualise algorithm operation.')

        # convert to dictionary
        self.args = vars(parser.parse_args())

        # set history flag
        if now == self.args['starttime']:
            self.fetch_history = False
        else:
            self.fetch_history = True


    def __set_filters(self):
        # historic events
        self.history_params = {
            'page_size': 1000,
            'start_time': self.args['starttime'],
            'end_time': self.args['endtime'],
            'event_types': ['temperature']
        }

        # stream events
        self.stream_params = {
            'event_types': ['temperature']
        }


    def __fetch_project_devices(self):
        # request list
        devices_list_url = "{}/projects/{}/devices".format(self.api_url_base,  self.project_id)
        device_listing = requests.get(devices_list_url, auth=(self.username, self.password))
        
        # remove fluff
        try:
            self.devices = device_listing.json()['devices']
        except KeyError as e:
            # an error here probably means connection issues
            print(e)
            hlp.print_error('Could not fetch devices.', terminate=True)


    def __spawn_devices(self):
        """
        Use list of devices to spawn a Desk- and Reference object.
        One Reference object in total and one Desk object per desk sensor.

        """

        # empty lists of devices
        self.desks      = {}
        self.reference  = Reference(self.args)

        # iterate list of devices
        for device in self.devices:
            # verify temperature type
            if device['type'] == 'temperature':
                # get device id
                device_id = os.path.basename(device['name'])

                # check if reference label is set
                if 'reference' in device['labels'].keys():
                    # append an initialised reference object
                    self.reference.add_device(device, device_id)
                else:
                    # append an initialised desk object
                    self.desks[device_id] = Desk(device, device_id, self.args)


    def __occupancy(self, current_timestamp):
        """
        Aggregate occupancy data of all sensors into a percentage.

        Parameters
        ----------
        current_timestamp : datetime
            UTC timestamp of latest event data in pandas datetime format.

        """

        # get current timestamp
        timestamp, _ = hlp.convert_event_data_timestamp(current_timestamp)

        # round timestamp to last hour and day
        timestamp_hour = timestamp.floor('H')
        timestamp_day  = timestamp.floor('D')

        # initialise if empty
        if len(self.hourly_occupancy_timestamp) == 0: 
            self.hourly_occupancy_timestamp.append(timestamp_hour)
            self.hourly_occupancy_percentage.append(None)
        if len(self.daily_occupancy_timestamp) == 0: 
            self.daily_occupancy_timestamp.append(timestamp_day + pd.Timedelta('12h'))
            self.daily_occupancy_percentage.append(None)

        # check if new hour
        if self.hourly_occupancy_timestamp[-1] != timestamp_hour:
            # update occupancy for last hour
            self.__update_hourly_occupancy()

            # append new hour
            self.hourly_occupancy_timestamp.append(timestamp_hour)
            self.hourly_occupancy_percentage.append(None)

        # check if new day
        if self.daily_occupancy_timestamp[-1].floor('D') != timestamp_day:
            # update daily occupancy (within working hours)
            self.__update_daily_occupancy()
            
            # append new day
            self.daily_occupancy_timestamp.append(timestamp_day + pd.Timedelta('12h'))
            self.daily_occupancy_percentage.append(None)


    def __update_hourly_occupancy(self):
        """
        Calculate occupancy percentage with hourly resolution.

        """

        # set zero
        self.hourly_occupancy_percentage[-1] = 0

        # iterate known desks
        for i, sid in enumerate(self.desks.keys()):
            # reset activity flag
            active = False

            # verify any data
            j = len(self.desks[sid].timestamp)
            if j > 0:
                # iterate back in time
                while not active and j > 0 and self.desks[sid].timestamp[j-1] >= self.hourly_occupancy_timestamp[-1]:
                    # check if occupancy triggered
                    if self.desks[sid].state[j-1] == 1:
                        active = True

                    # iterate backwards
                    j -= 1

            # add to sum if active
            if active:
                self.hourly_occupancy_percentage[-1] += 1

        # normalise to a percentage
        self.hourly_occupancy_percentage[-1] = (self.hourly_occupancy_percentage[-1] / len(self.desks)) * 100


    def __update_daily_occupancy(self):
        """
        Calculate occupancy percentage daily resolution.

        """

        # set zero
        self.daily_occupancy_percentage[-1] = 0

        # median percentage list
        median_percentage = []

        # iterate back in time 1 day
        i = len(self.hourly_occupancy_timestamp)
        while i > 0 and self.hourly_occupancy_timestamp[i-1] >= self.daily_occupancy_timestamp[-1].floor('D'):
            # set working hours
            t1 = self.daily_occupancy_timestamp[-1].floor('D') + pd.Timedelta('{}h'.format(params['occupancy']['working_hours'][0]))
            t2 = self.daily_occupancy_timestamp[-1].floor('D') + pd.Timedelta('{}h'.format(params['occupancy']['working_hours'][1]))
        
            # only use working hours
            if self.hourly_occupancy_timestamp[i-1] >= t1 and self.hourly_occupancy_timestamp[i-1] <= t2:
                median_percentage.append(self.hourly_occupancy_percentage[i-1])
            
            # iterate
            i -= 1

        # set daily value
        self.daily_occupancy_percentage[-1] = np.median(median_percentage)


    def __fetch_event_history(self):
        # initialise empty event list
        self.event_history = []

        # iterate devices
        for device in self.devices:
            # isolate device identifier
            device_id = os.path.basename(device['name'])
        
            # some printing
            print('-- Getting event history for {}'.format(device_id))
        
            # initialise next page token
            self.history_params['page_token'] = None
        
            # set endpoints for event history
            event_list_url = "{}/projects/{}/devices/{}/events".format(self.api_url_base, self.project_id, device_id)
        
            # perform paging
            while self.history_params['page_token'] != '':
                event_listing = requests.get(event_list_url, auth=(self.username, self.password), params=self.history_params)
                event_json = event_listing.json()
        
                try:
                    self.history_params['page_token'] = event_json['nextPageToken']
                    self.event_history += event_json['events']
                except KeyError:
                    hlp.print_error('Page token lost. Please try again.', terminate=True)
        
                if self.history_params['page_token'] is not '':
                    print('\t-- paging')
        
        # sort event history in time
        self.event_history.sort(key=hlp.json_sort_key, reverse=False)


    def event_history(self):
        # do nothing if starttime not given
        if not self.fetch_history:
            return

        # get list of hsitoric events
        self.__fetch_event_history()
        
        # estimate occupancy for history 
        cc = 0
        for i, event_data in enumerate(self.event_history):
            cc = hlp.loop_progress(cc, i, len(self.event_history), 25, name='event history')
            # serve event to director
            self.__new_event_data(event_data, cout=False)
        
        # initialise plot
        if self.args['plot']:
            print('\nClose the blocking plot to start stream.')
            print('A new non-blocking plot will appear for stream.')
            self.initialise_plot()
            self.plot_progress(blocking=True)
        # plot debug
        elif self.args['debug']:
            self.initialise_debug_plot()
            self.plot_debug()


    def event_stream(self, n_reconnects=5):
        # cout
        print("Listening for events... (press CTRL-C to abort)")
    
        # reinitialise plot
        if self.args['plot']:
            self.initialise_plot()
            self.plot_progress(blocking=False)
    
        # loop indefinetly
        nth_reconnect = 0
        while nth_reconnect < n_reconnects:
            try:
                # reset reconnect counter
                nth_reconnect = 0
        
                # get response
                response = requests.get(self.stream_endpoint, auth=(self.username, self.password), headers={'accept':'text/event-stream'}, stream=True, params=self.stream_params)
                client = sseclient.SSEClient(response)
        
                # listen for events
                print('Connected.')
                for event in client.events():
                    # new data received
                    event_data = json.loads(event.data)['result']['event']
        
                    # serve event to director
                    self.__new_event_data(event_data)
        
                    # plot progress
                    if self.args['plot']:
                        self.plot_progress(blocking=False)
            
            # catch errors
            # Note: Some VPNs seem to cause quite a lot of packet corruption (?)
            except requests.exceptions.ConnectionError:
                nth_reconnect += 1
                print('Connection lost, reconnection attempt {}/{}'.format(nth_reconnect, n_reconnects))
            except requests.exceptions.ChunkedEncodingError:
                nth_reconnect += 1
                print('An error occured, reconnection attempt {}/{}'.format(nth_reconnect, n_reconnects))
            
            # wait 1s before attempting to reconnect
            time.sleep(1)


    def print_devices_information(self):
        """
        Print information about active devices in stream.

        """

        print('\nDirector initialised for devices:')
        # print desks
        for desk in self.desks:
            print('-- {:<30}{}'.format(desk, 'desk'))
        for device in self.reference.devices:
            print('-- {:<30}{}'.format(device, 'reference'))
        print()


    def __new_event_data(self, event_data, cout=True):
        """
        Receive new event_data json and pass it along to the correct device object.

        Parameters
        ----------
        event_data : dictionary
            Data json containing new event data.

        """

        # get id of source sensor
        source_id = os.path.basename(event_data['targetName'])

        # verify temperature event
        if 'temperature' in event_data['data'].keys():
            # check if source device is known
            if source_id in self.desks.keys():
                # serve event to desk
                self.desks[source_id].new_event_data(event_data, self.reference.latest_value)
                if cout: print('-- {:<30}{}'.format(source_id, 'desk'))

            elif source_id in self.reference.devices.keys():
                # serve new temperature value to reference
                self.reference.new_event_data(event_data, source_id)
                if cout: print('-- {:<30}{}'.format(source_id, 'reference'))

            # update occupancy stats
            self.__occupancy(event_data['data']['temperature']['updateTime'])


    def initialise_plot(self):
        """
        Create figure object used in results visualization.

        """

        self.fig, self.ax = plt.subplots(3, 1, sharex=True)


    def initialise_debug_plot(self):
        """
        Create figure object used in debug visualization.

        """

        self.dfig, self.dax = plt.subplots(4, 1, sharex=False)


    def plot_progress(self, blocking):
        """
        Plot the stream and all its devices with desk occupancy status.

        """

        # refresh figure
        self.ax[0].cla()
        self.ax[1].cla()
        self.ax[2].cla()

        # plot all desks
        for i, desk in enumerate(self.desks):
            color = stl.wheel[i%len(stl.wheel)]
            self.ax[0].plot(self.desks[desk].timestamp, self.desks[desk].temperature,             '-', color=color, label=desk)
            self.ax[1].plot(self.desks[desk].timestamp, np.array(self.desks[desk].state) + i*1.5, '-', color=color, label=desk)
        self.ax[0].set_ylabel('Temperature [deg]')
        self.ax[1].set_ylabel('Occupancy State')

        # plot reference
        self.ax[0].plot(self.reference.timestamp, self.reference.temperature, '.-', color=stl.VB[1], linewidth=2,  label='reference')
        # self.ax[0].legend(loc='upper left')
        
        # plot occupancies
        self.ax[2].plot(self.hourly_occupancy_timestamp, self.hourly_occupancy_percentage, '-',  linewidth=2, label='Hourly Occupancy', color=stl.NS[1])
        self.ax[2].plot(self.daily_occupancy_timestamp,  self.daily_occupancy_percentage,  '.-', linewidth=3, label='Daily Occupancy', color=stl.SS[1])
        self.ax[2].legend(loc='upper right')
        self.ax[2].set_ylim([0, 100])
        self.ax[2].set_ylabel('Occupancy [%]')
        self.ax[2].set_xlabel('Timestamp')

        if blocking:
            # self.ax[0].set_title('Blocking Visualisation.')
            plt.show()
        else:
            self.ax[0].set_title('Non-Blocking Visualisation.')
            plt.pause(0.001)


    def plot_debug(self):
        """
        Plot more information regarding algorithm operation per device after event history only.

        """

        # iterate desks
        print('\nDEBUG')
        print('Close plots to see next sensor.')
        for desk in self.desks:
            # re-initialise figure
            self.initialise_debug_plot()

            print(desk)
            self.dax[0].cla()
            self.dax[0].plot(self.desks[desk].timestamp, self.desks[desk].temperature, '-', color=stl.NS[1], linewidth=stl.lw, label='Desk Temperature')
            self.dax[0].plot(self.reference.timestamp,   self.reference.temperature,   '-', color=stl.SS[1], linewidth=stl.lw, label='Reference Temperature')
            self.dax[0].set_title(desk)
            self.dax[0].set_xlabel('Timestamp')
            self.dax[0].set_ylabel('Temperature [deg]')
            self.dax[0].legend(loc='upper left')

            self.dax[1].cla()
            self.dax[1].plot(self.desks[desk].timestamp, self.desks[desk].diff,      '-', color=stl.NS[1], linewidth=stl.lw, label='Differenced Temperature')
            self.dax[1].plot(self.desks[desk].timestamp, self.desks[desk].dsl_thrs, '-', color=stl.SS[1], linewidth=stl.lw, label='Downslope Threshold')
            self.dax[1].set_xlabel('Timestamp')
            self.dax[1].set_ylabel('Temperature [deg]')
            self.dax[1].legend(loc='upper left')

            self.dax[2].cla()
            self.dax[2].plot(self.desks[desk].timestamp, self.desks[desk].roc,      '-', color=stl.NS[1], linewidth=stl.lw, label='Rate of Change')
            self.dax[2].plot(self.desks[desk].timestamp, self.desks[desk].roc_thrs, '-', color=stl.SS[1], linewidth=stl.lw, label='Dynamic Threshold')
            self.dax[2].set_xlabel('Timestamp')
            self.dax[2].set_ylabel('Temperature [deg/min]')
            self.dax[2].legend(loc='upper left')

            self.dax[3].cla()
            n = len(self.desks[desk].state)
            self.dax[3].fill_between(self.desks[desk].timestamp[-n:], np.zeros(n), self.desks[desk].state, alpha=0.75, color=stl.SS[1], label='Detected Occupancy')
            self.dax[3].plot(self.desks[desk].timestamp[:], self.desks[desk].state,      '-', color=stl.NS[1], linewidth=stl.lw, label='No Occupancy')
            self.dax[3].set_xlabel('Timestamp')
            self.dax[3].set_ylabel('Binary')
            self.dax[3].legend(loc='upper left')

            plt.show()
        
