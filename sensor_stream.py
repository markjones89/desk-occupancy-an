# packages
import sys

# project
import occupancy.interface as interface
from occupancy.director import Director


# Fill in from the Service Account and Project:
username="brn1e6r24te000b24bp0"             # this is the key
password="34fc21309a8e462cb491a0d7610ea489" # this is the secret
project_id="brn0ti14jplfqcpojb60"            # this is the project id

# url base and endpoint
api_url_base  = "https://api.disruptive-technologies.com/v2"
devices_stream_url="{}/projects/{}/devices:stream".format(api_url_base, project_id)


if __name__ == '__main__':
    # parse arguments
    args, history = interface.parse_arguments()

    # set filters for event history and stream
    event_params  = {'page_size': 1000, 'start_time': args['starttime'], 'end_time': args['endtime'], 'event_types': ['temperature']}
    stream_params = {'event_types': ['temperature']}

    # Get list of Devices in Project via API
    devices = interface.get_devices(project_id, username, password, api_url_base)

    # initialise Director with devices list
    d = Director(devices, args)

    # get devices event history
    if history:
        d = interface.event_history_stream(d, devices, args, project_id, username, password, event_params, api_url_base)

    # Listen to all events from all Devices in Project via API
    interface.stream(d, args, username, password, devices_stream_url, stream_params, n_reconnects=5)


