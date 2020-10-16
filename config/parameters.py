
params = {
    'roc': {
        'gamma_max':    0.075,      # ROC threshold maximum value
        'gamma_min':    0.010,      # ROC threshold minimum value
        'beta':         0.003,      # ROC threshold positive increase per minute
        'alpha':        0.500,      # ROC threshold pulldown percentage of current roc
    },

    'diff': {
        'longest_avg_lookback':     60*60*1     # [seconds] how much data to use when averaging for threshold
    },

    'occupancy': {
        'working_hours':    [8, 16],
    }
}

