
params = {
    'roc': {
        'thrs_maxval':          0.075,      # ROC threshold maximum value
        'thrs_minval':          0.010,      # ROC threshold minimum value
        'thrs_posdiff':         0.003,      # ROC threshold positive increase per minute
        'pulldown_modifier':    0.500,      # ROC threshold pulldown percentage of current roc
    },

    'diff': {
        'longest_avg_lookback':     60*60*1     # [seconds] how much data to use when averaging for threshold
    },

    'occupancy': {
        'working_hours':    [8, 16],
    }
}

