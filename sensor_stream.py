# packages
import os
import sys
import json
import time
import pprint
import argparse
import requests
import datetime
import sseclient

# project
import occupancy.helpers as helpers
from occupancy.director  import Director

# Fill in from the Service Account and Project:
username="brn1e6r24te000b24bp0"             # this is the key
password="34fc21309a8e462cb491a0d7610ea489" # this is the secret
project_id="brn0ti14jplfqcpojb60"            # this is the project id

# set url base
api_url_base  = "https://api.disruptive-technologies.com/v2"


def json_sort_key(json):
    """
    Return the event update time converted to unixtime.

    Parameters
    ----------
    json : dictionary
        Event data json imported as dictionary.

    Returns
    -------
    unixtime : int
        Event data update time converted to unixtime.

    """

    timestamp = json['data']['temperature']['updateTime']
    _, unixtime = helpers.convert_event_data_timestamp(timestamp)
    return unixtime


def get_event_history():
    """
    Get events in history from DT Studio project.

    Returns
    -------
    events : list
        List of historic events jsons.

    Notes
    -----
    The paging process has been known to fail when certain VPNs are enabled.
    Try disabling VPN if page token is continously lost.

    """

    # initialise empty event list
    events = []

    # iterate devices
    for device in devices:
        # isolate device identifier
        device_id = os.path.basename(device['name'])
    
        # some printing
        print('-- Getting event history for {}'.format(device_id))
    
        # initialise next page token
        event_params['page_token'] = None
    
        # set endpoints for event history
        event_list_url = "{}/projects/{}/devices/{}/events".format(api_url_base, project_id, device_id)
    
        # perform paging
        while event_params['page_token'] != '':
            event_listing = requests.get(event_list_url, auth=(username, password), params=event_params)
            event_json = event_listing.json()
    
            try:
                event_params['page_token'] = event_json['nextPageToken']
                events += event_json['events']
            except KeyError:
                helpers.print_error('Page token lost. Please try again.', terminate=True)
    
            if event_params['page_token'] is not '':
                print('\t-- paging')
    
    # sort event history in time
    events.sort(key=json_sort_key, reverse=False)

    return events


def parse_arguments():
    """
    Parse for command line arguments.

    Returns
    -------
    arguments : dictionary
        Dictionary of arguments and their values added by parses.
    history : boolean
        Whether or not historic event data should be fetched from project.

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
    arguments = vars(parser.parse_args())

    # set history flag
    if now == arguments['starttime']:
        history = False
    else:
        history = True

    return arguments, history


def get_devices():
    """
    Get list of devices in project.

    Returns
    -------
    devices : list
        List of dictionaries containing information about devices in project.

    """

    # format the url
    devices_list_url = "{}/projects/{}/devices".format(api_url_base,  project_id)

    # request the device list
    device_listing   = requests.get(devices_list_url, auth=(username, password))
    
    # remove fluff
    try:
        devices = device_listing.json()['devices']
    except KeyError:
        # probably connection issues if we error here
        helpers.print_error(device_listing.json(), terminate=True)

    return devices


def event_history_stream():  
    """
    Iterate through and estimate occupancy on event history.

    """

    # get list of events
    events = get_event_history()
    
    # estimate occupancy for history 
    cc = 0
    for i, event_data in enumerate(events):
        cc = helpers.loop_progress(cc, i, len(events), 25, name='event history')
        # serve event to director
        d.new_event_data(event_data, cout=False)
    
    # initialise plot
    if args['plot']:
        print('\nClose the blocking plot to start stream.')
        print('A new non-blocking plot will appear for stream.')
        d.initialise_plot()
        d.plot_progress(blocking=True)
    # plot debug
    elif args['debug']:
        d.initialise_debug_plot()
        d.plot_debug()


def stream(n_reconnects=5):
    """
    Listen for new streaming events.

    Parameters
    ----------
    n_reconnects : int
        Maximum number of reconnects on connection loss.

    Notes
    -----
    The listening process has been known to fail when certain VPNs are enabled.
    Try disabling VPN if exceptions are thrown often.

    """

    # cout
    print("Listening for events... (press CTRL-C to abort)")

    # reinitialise plot
    if args['plot']:
        d.initialise_plot()
        d.plot_progress(blocking=False)

    # loop indefinetly
    nth_reconnect = 0
    while nth_reconnect < n_reconnects:
        try:
            # reset reconnect counter
            nth_reconnect = 0
    
            # get response
            response = requests.get(devices_stream_url, auth=(username,password),headers={'accept':'text/event-stream'}, stream=True, params=stream_params)
            client = sseclient.SSEClient(response)
    
            # listen for events
            print('Connected.')
            for event in client.events():
                # new data received
                event_data = json.loads(event.data)['result']['event']
    
                # serve event to director
                d.new_event_data(event_data)
    
                # plot progress
                if args['plot']:
                    d.plot_progress(blocking=False)
        
        # catch errors
        # Note: Some VPNs seem to cause quite a lot of packet corruption (?)
        except requests.exceptions.ConnectionError:
            nth_reconnect += 1
            print('Connection lost, reconnection attempt {}/{}'.format(nth_retry, MAX_RETRIES))
        except requests.exceptions.ChunkedEncodingError:
            nth_reconnect += 1
            print('An error occured, reconnection attempt {}/{}'.format(nth_retry, MAX_RETRIES))
        
        # wait 1s before attempting to reconnect
        time.sleep(1)


if __name__ == '__main__':
    # parse arguments
    args, history = parse_arguments()

    # set filters for event history and stream
    event_params  = {'page_size': 1000, 'start_time': args['starttime'], 'end_time': args['endtime'], 'event_types': ['temperature']}
    stream_params = {'event_types': ['temperature']}

    # Get list of Devices in Project via API
    devices = get_devices()

    # initialise Director with devices list
    d = Director(devices, args)

    # generate endpoints for stream
    devices_stream_url="{}/projects/{}/devices:stream".format(api_url_base, project_id)

    # get devices event history
    if history:
        event_history_stream()

    # Listen to all events from all Devices in Project via API
    stream(n_reconnects=5)


