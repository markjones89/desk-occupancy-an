# packages
import os
import json
import requests
import datetime
import argparse
import sseclient

# project
import occupancy.helpers as helpers


def parse_arguments():
    """
    Parse for command line arguments.

    Returns
    -------
    arguments : dictionary
        Dictionary of arguments and their values added by parses.
    history : bool
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


def get_devices(project_id, username, password, api_url_base):
    """
    Get list of devices in project.

    Parameters
    ----------
    project_id : str
        DT Studio project identifier.
    username : str
        Service account key.
    password : str
        Service account secret.
    api_url_base : str
        Base API url.

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


def get_event_history(devices, project_id, username, password, event_params, api_url_base):
    """
    Get events in history from DT Studio project.

    Parameters
    ----------
    devices : list
        List of devices dictionaries.
    project_id : str
        DT Studio project identifier.
    username : str
        Service account key.
    password : str
        Service account secret.
    event_params : dictionary
        Filters used when fetching events from project.
    api_url_base : str
        Base API url.

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
    events.sort(key=helpers.json_sort_key, reverse=False)

    return events


def event_history_stream(d, devices, args, project_id, username, password, event_params, api_url_base):  
    """
    Iterate through and estimate occupancy on event history.

    Parameters
    ----------
    d : object
        Director object instance.
    devices : list
        List of devices dictionaries.
    args : dictionary
        Dictionary of system arguments and their parsed values.
    project_id : str
        DT Studio project identifier.
    username : str
        Service account key.
    password : str
        Service account secret.
    event_params : dictionary
        Filters used when fetching events from project.
    api_url_base : str
        Base API url.

    Returns
    -------

    """

    # get list of events
    events = get_event_history(devices, project_id, username, password, event_params, api_url_base)
    
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

    return d


def stream(d, args, username, password, devices_stream_url, stream_params, n_reconnects=5):
    """
    Listen for new streaming events.

    Parameters
    ----------
    d : object
        Director object instance.
    args : dictionary
        Dictionary of system arguments and their parsed values.
    username : str
        Service account key.
    password : str
        Service account secret.
    stream_params : dictionary
        Filters used when streaming events from project.
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

