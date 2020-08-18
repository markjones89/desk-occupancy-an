# Desk Occupancy

## What am I?
This repository contains the example code talked about in [this application note (LINK PENDING)](https://www.disruptive-technologies.com/) proposing a method of using the Disruptive Technologies (DT) Temperature Sensor for desk occupancy tracking. Written in Python 3, it implements the DT Developer API to communicate with a DT Studio project and its sensors. By calling sensor_stream.py, an estimate of desk occupancy will be calculated for previous history data and/or a live stream of datapoints from the moment of execution.

## Before Running Any code
A DT Studio project containing desk- and reference temperature sensors should be made. All temperature sensors in the project will be assumed part of the desk occupancy estimation.

For best performance, the [Wireless Temperature Sensor EN12830/330s](https://support.disruptive-technologies.com/hc/en-us/articles/360010452139-Wireless-Temperature-Sensor-EN12830-330s), sampling at 5.5 minute intervals should be used. The [Wireless Temperature Sensor](https://support.disruptive-technologies.com/hc/en-us/articles/360010342900-Wireless-Temperature-Sensor) will also work, but the lower sampling rate might reduce accuracy significantly.

Under each desk, a temperature sensor should be placed where it is most likely a person will sit. Closer to the edge is better.

(Recommended) For increased accuracy, one- or several temperature sensors can be used to track reference ambient temperature. These should be placed on a wall away from any window/sun, preferably at standing height. It should be away from any heat sources like air-condition vents or coffee machines etc.  
Reference sensors should be given the label "reference" in the DT Studio project. If not it will be assumed to be a desk sensor.

## Environment Setup
Install dependencies.
```
pip install -r requirements.txt
```

Edit *sensor_stream.py* to provide the following authentication details of your project. Information about setting up your project for API authentication can be found in this [streaming API guide](https://support.disruptive-technologies.com/hc/en-us/articles/360012377939-Using-the-stream-API).
```python
USERNAME   = "SERVICE_ACCOUNT_KEY"       # this is the key
PASSWORD   = "SERVICE_ACCOUT_SECRET"     # this is the secret
PROJECT_ID = "PROJECT_ID"                # this is the project id
```

## Usage
Running *python3 sensor_stream.py* will start streaming data from the sensors in your project for which desk occupancy will be estimated for either historic data using *--starttime* flag, a stream, or both. Provide the *--plot* flag to visualise the results. 
```
usage: sensor_stream.py [-h] [--starttime] [--endtime] [--plot] [--debug]

Desk Occupancy Estimation on Stream and Event History.

optional arguments:
  -h, --help    show this help message and exit
  --starttime   Event history UTC starttime [YYYY-MM-DDTHH:MM:SSZ].
  --endtime     Event history UTC endtime   [YYYY-MM-DDTHH:MM:SSZ].
  --plot        Plot the estimated desk occupancy.
  --debug       Visualise algorithm operation.
```

Note: When using the *--starttime* argument for a date far back in time, if many sensors exist in the project, the paging process might take several minutes.


