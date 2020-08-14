# packages
import sys
import argparse
import numpy  as np
import pandas as pd


def convert_event_data_timestamp(ts):
    """
    Convert the default event_data timestamp format to Pandas and unixtime format.

    Parameters
    ----------
    ts : str
        UTC timestamp in custom API event data format.

    Returns
    -------
    timestamp : datetime
        Pandas Timestamp object format.
    unixtime : int
        Integer number of seconds since 1 January 1970.

    """

    timestamp = pd.to_datetime(ts)
    unixtime  = pd.to_datetime(np.array([ts])).astype(int)[0] // 10**9

    return timestamp, unixtime


def temperature_roc_per_minute(dt, dy):
    """
    Convert a delta time and delta temperature to rate of change in deg/min.

    Parameters
    ----------
    dt : int
        Delta unixtime.
    dy : int
        Delta temperature.

    Returns
    -------
    return : float
        Positive rate of change in deg/min.

    """

    return max(0, (dy / dt) * 60)


def print_error(text, terminate=True):
    """
    Print an error message and terminate as desired.

    Parameters
    ----------
    terminate : bool
        Terminate execution if True.
    """

    print('ERROR: {}'.format(text))
    if terminate:
        sys.exit()


def loop_progress(i_track, i, n_max, n_steps, name=None, acronym=' '):
    """
    Print loop progress to console.

    Parameters
    ----------
    i_track : int
        Tracks how far the progress has come:
    i : int
        Current index in loop.
    n_max : int
        Maximum value which indicates progress done.
    n_steps : int
        Number of steps to be counted.

    """

    # number of indices in each progress element
    part = n_max / n_steps

    if i_track == 0:
        # print empty bar
        print('    |')
        if name is None:
            print('    └── Progress:')
        else:
            print('    └── {}:'.format(name))
        print('        ├── [ ' + (n_steps-1)*'-' + ' ] ' + acronym)
        i_track = 1
    elif i > i_track + part:
        # update tracker
        i_track = i_track + part

        # print bar
        print('        ├── [ ' + int(i_track/part)*'#' + (n_steps - int(i_track/part) - 1)*'-' + ' ] ' + acronym)

    # return tracker
    return i_track

