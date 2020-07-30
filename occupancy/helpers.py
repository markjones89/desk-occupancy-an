# packages
import sys
import argparse
import numpy  as np
import pandas as pd

def convert_event_data_timestamp(ts):
    """Convert the default event_data timestamp format to Pandas and unixtime format.

    Parameters:
        ts -- event_data timestamp format

    Returns:
        timestamp -- Pandas Timestamp object format.
        unixtime  -- Integer number of seconds since 1 January 1970.

    """

    timestamp = pd.to_datetime(ts)
    unixtime  = pd.to_datetime(np.array([ts])).astype(int)[0] // 10**9

    return timestamp, unixtime


def temperature_roc_per_minute(dt, dy):
    """Convert a delta time and delta temperature to rate of change in deg/min.

    Parameters:
        dt -- Change in time.
        dy -- Change in temperature.

    Returns:
        Positive rate of change in deg/min.
    """

    return max(0, (dy / dt) * 60)


def print_error(text, terminate=True):
    """Print an error message and terminate as desired.

    Parameters:
        terminate -- Terminate execution if True.
    """

    print('ERROR: {}'.format(text))
    if terminate:
        sys.exit()


def loop_progress(i_track, i, N_max, N_steps, name=None, acronym=' '):
    """ print progress to console

    arguments:
    i_track:    tracks how far the progress has come:
    i:          what the current index is.
    N_max:      the maximum value which indicates progress done.
    N_steps:    how many steps which are counted.
    """

    # number of indices in each progress element
    part = N_max / N_steps

    if i_track == 0:
        # print empty bar
        print('    |')
        if name is None:
            print('    └── Progress:')
        else:
            print('    └── {}:'.format(name))
        print('        ├── [ ' + (N_steps-1)*'-' + ' ] ' + acronym)
        i_track = 1
    elif i > i_track + part:
        # update tracker
        i_track = i_track + part

        # print bar
        print('        ├── [ ' + int(i_track/part)*'#' + (N_steps - int(i_track/part) - 1)*'-' + ' ] ' + acronym)

    # return tracker
    return i_track

