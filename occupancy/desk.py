import numpy as np


class Desk():

    # Config parameters to control behavior.
    window_seconds = 60*2.5
    roc_upper_threshold = +0.11
    roc_threshold_delay_s = 120

    def __init__(self, device_id):
        # Set parameter attributes.
        self.device_id = device_id

        # Initialize data lists.
        self.timestamps = []
        self.celsius = []

        # Initialize supporting lists.
        self.roc = []
        self.gamma = []
        self.state_array = []

        # Initialize a variable for indicating window start.
        self.roc_i = 0

        # Variables for other stuff.
        self.n_samples = 0
        self.occupied = False
        self.lag = 0

    def _append_data(self, timestamp, celsius):
        self.timestamps.append(timestamp)
        self.celsius.append(celsius)
        self.roc.append(0)
        self.state_array.append(0)
        self.n_samples += 1

        # Update window start position.
        dt = self.timestamps[-1] - self.timestamps[self.roc_i]
        while dt.total_seconds() > self.window_seconds:
            self.roc_i += 1
            dt = self.timestamps[-1] - self.timestamps[self.roc_i]

    def new_sample(self, timestamp, celsius):
        # Append data to data lists.
        self._append_data(timestamp, celsius)

        # Half if not enough samples.
        if self.n_samples < 2:
            return

        # Calculate new rate of change value.
        minmax = [
            np.argmax(self.celsius[self.roc_i:]) + self.roc_i,
            np.argmin(self.celsius[self.roc_i:]) + self.roc_i,
        ]
        self.roc[-1] = (self.celsius[max(minmax)] - self.celsius[min(minmax)])

        # Iterate core algorithm.
        self._iterate_core()

    def _iterate_core(self):

        # Determine action based on state.
        if self.occupied:
            # Check if we're still above threshold.
            if self.roc[-1] >= 0:
                self.state_array[-1] = 1
                self.lag = 0

            else:
                self.lag += 1

                # Check if we've been negative for long enough.
                dt = self.timestamps[-1] - self.timestamps[-self.lag]
                if dt.total_seconds() >= self.roc_threshold_delay_s:
                    self.occupied = False
                    self.lag = 0

        else:
            # If first lag we must pass ROC threshold.
            if self.lag >= 0 and self.roc[-1] >= self.roc_upper_threshold:
                self.lag += 1

                # Check if we've been positive for long enough.
                dt = self.timestamps[-1] - self.timestamps[-self.lag]
                if dt.total_seconds() >= self.roc_threshold_delay_s:
                    self.occupied = True
                    self.state_array[-1] = 1
                    self.lag = 0

            # Otherwise, being positive is enough.
            elif self.lag > 0 and self.roc[-1] >= 0:
                self.lag += 1

                # Check if we've been positive for long enough.
                dt = self.timestamps[-1] - self.timestamps[-self.lag]
                if dt.total_seconds() >= self.roc_threshold_delay_s:
                    self.occupied = True
                    self.state_array[-1] = 1
                    self.lag = 0

            else:
                self.lag = 0
