from datetime import datetime, timedelta

import pandas as pd
import disruptive as dt

from occupancy import cout


def authenticate(args):
    dt.default_auth = dt.Auth.service_account(
        key_id=args.key_id,
        secret=args.secret,
        email=args.email,
    )


def fetch_event_history(args):
    # Construct labels dictionary based on argument.
    if args.label is None:
        label = {}
    else:
        label = {args.label: ''}

    # Fetch list of devices in project.
    devices = dt.Device.list_devices(
        project_id=args.project_id,
        label_filters=label,
        device_types=[dt.Device.TEMPERATURE],
    )

    # Initialize dictionary which will hold a field for each device.
    history = {}

    # Iterate devices and fetch their event history.
    for device in devices:
        events = dt.EventHistory.list_events(
            device_id=device.device_id,
            project_id=args.project_id,
            event_types=[dt.events.TEMPERATURE],
            start_time=datetime.utcnow() - timedelta(days=args.days),
        )
        cout.device_events(device.device_id, len(events))

        # Reset columns list.
        cols = []

        # Iterate each event in list.
        for event in events:
            # Iterate each sample in event.
            for sample in event.data.samples:
                # Append columns list.
                cols.append([
                    sample.timestamp,
                    sample.celsius,
                ])

        # Convert to dataframe, then sort ascending.
        cols_df = pd.DataFrame(cols, columns=['timestamp', 'celsius'])
        cols_df.set_index('timestamp', inplace=True, drop=True)
        cols_df.index = pd.to_datetime(cols_df.index)
        cols_df.sort_index(ascending=True, inplace=True)

        # Add new entry to dictionary.
        history[device.device_id] = {
            'timestamp': cols_df.index,  # pandas datetime format
            'celsius': cols_df.celsius,
            'n': len(cols_df),
        }

    return history
