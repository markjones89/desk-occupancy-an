# Desk Occupancy Application Note
This repository contains example code related to [this application note](https://developer.disruptive-technologies.com/docs/other/application-notes/desk-occupancy-monitoring-using-temperature-sensors), where a method of using Disruptive Technologies (DT) Wireless Temperature Sensors for desk occupancy monitoring is showcased.

## Preliminaries
Note that this implementation aims to get you started with desk occupancy monitoring. It is not meant to be used as a finished product but rather showcase one method of getting started with developing your own solution.

## Usage
Running the `example.py` script with the `--sample` and `--plog-agg` optional arguments will estimate occuancy on all provided sample data, then plot the aggregated results.

```bash
python3 example.py --sample --plot-agg
```

### Pulling Your Own Data
By providing the Service Account credentials set up earlier, the implementation will pull (by default 7 days) data from all sensors in the specified project.

```bash
python3 example.py --project_id "<PROJECT_ID>" \
                   --key_id "<KEY_ID>" \
                   --secret "<SECRET>" \
                   --email "<EMAIL>" \
                   --days 7 \
                   --plot-agg
```

### Additional Configurations
See `python3 example.py -h` for more optional arguments.

```bash
optional arguments:
  -h, --help     show this help message and exit
  --key-id       Service Account Key ID
  --secret       Service Account Secret
  --email        Service Account Email
  --project-id   Identifier of project where devices are held.
  --label        Only fetches sensors with provided label key.
  --days         Days of event history to fetch.
  --sample       Use provided sample data.
  --plot-desks   Plot each individual desk results.
  --plot-agg     Plot aggregated results
```
