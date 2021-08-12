import os

import pandas as pd

from occupancy import cout

ABS_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(ABS_DIR, '..', 'data')


def from_provided(args):
    # Initialize events dictionary.
    history = {}

    # List files in directory.
    for f in os.listdir(DATA_DIR):
        # Filter for .csv files.
        if not f.endswith('.csv'):
            continue

        # Read file to DataFrame.
        df = pd.read_csv(os.path.join(DATA_DIR, f))

        # Isolate device ID from filename.
        xid = f.split('.')[0]

        # Sort timestamps ascending.
        df.set_index('timestamp', inplace=True, drop=True)
        df.index = pd.to_datetime(df.index)
        df.sort_index(ascending=True, inplace=True)

        # Add new entry to dictionary.
        history[xid] = {
            'timestamp': df.index,  # pandas datetime format
            'celsius': df.temperature,
            'n': len(df),
        }

        # Print some information.
        cout.device_events(xid, len(df))

    return history
