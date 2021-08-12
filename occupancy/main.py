import occupancy as oc

from progress.bar import Bar


def main():
    # Parse system arguments provided by user.
    args = oc.interface.parse_sysargs()

    # Print argument configuration to console.
    oc.cout.config(args)

    # Fetch historic events on which occupancy will be estimated.
    print('\nPulling historic samples:\n' + '-'*31)
    if args.sample:
        # Use provided sample data.
        history = oc.sample.from_provided(args)
    else:
        # Authenticate towards the API.
        oc.api.authenticate(args)

        # Pull event history from the API.
        history = oc.api.fetch_event_history(args)

    # Initialize list that will hold desk objects.
    desks = {}

    # Iterate each device in history.
    print('\nEstimating occupancy on history:\n' + '-'*32)
    for device_id in history:
        # Add desk entry for device.
        desks[device_id] = oc.desk.Desk(device_id)

        # Iterate each sample for device.
        with Bar(device_id, max=history[device_id]['n']) as bar:
            for i in range(history[device_id]['n']):
                # Provide new sample to Desk object, iterating algorithm.
                desks[device_id].new_sample(
                    timestamp=history[device_id]['timestamp'][i],
                    celsius=history[device_id]['celsius'][i],
                )

                # Iterate progress bar.
                bar.next()

        # Plot desk results.
        if args.plot_desks:
            oc.plot.single(desks[device_id])

    # Plot aggregated results.
    if args.plot_agg:
        oc.plot.aggregated(desks)
