# Desk Occupancy Application Note
This repository contains example code related to [this application note](https://developer.disruptive-technologies.com/docs/other/application-notes/desk-occupancy-monitoring-using-temperature-sensors), where a method of using Disruptive Technologies (DT) Wireless Temperature Sensors for desk occupancy monitoring is showcased.

## Preliminaries
This implementation aims to get you started with desk occupancy monitoring. It is is no way meant to be used as a finished product, but rather as a springboard for further development.

## Usage
The implementation can be tested using either the provided sample data, or data from your own installation.

### Provided Sample Data
Running the `example.py` script with the `--sample` flag requires no additional configuration and uses the provided sample data found in the `data/` directory.

```bash
python3 example.py --sample
```

### Pulling Your Own Data
To use your own data, make sure you have a working [Service Account](https://developer.disruptive-technologies.com/docs/service-accounts/introduction-to-service-accounts). Once set, authentication credentials can be provided to the script.

```bash
python3 example.py --key_id "<KEY_ID>" --secret "<SECRET>" --email "<EMAIL>"
```

### Additional Configurations
See `python3 example.py -h`.
