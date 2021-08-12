import pandas as pd
import matplotlib.pyplot as plt


def single(desk):
    plt.figure()
    trig = []
    for i in range(desk.n_samples):
        if desk.state_array[i] == 1:
            trig.append(desk.celsius[i])
        else:
            trig.append(None)

    k1 = plt.subplot(211)
    k1.plot(desk.timestamps, desk.celsius, label='Raw Temperature')
    k1.plot(desk.timestamps, trig, 'r', label='Occupied')
    plt.ylabel('Celsius')
    plt.legend()
    k2 = plt.subplot(212, sharex=k1)
    k2.plot(desk.timestamps, desk.roc, '.-', label='ROC')
    k2.axhline(0, color='k')
    k2.axhline(desk.roc_upper_threshold, color='r', label='ROC Threshold')
    plt.xlabel('Timestamp')
    plt.ylabel('Rate of Change')
    plt.legend()
    plt.pause(0.001)


def aggregated(desks):
    plt.figure()

    def aggregate_by(desks, rate):
        agg = None
        for d in desks:
            df = pd.DataFrame(
                [
                    [desks[d].timestamps[i], desks[d].state_array[i]]
                    for i in range(desks[d].n_samples)
                ],
                columns=['timestamp', 'state'],
            )
            df.set_index('timestamp', drop=True, inplace=True)
            df = df.resample(rate).state.max()

            if agg is None:
                agg = df.copy()
            else:
                agg = pd.concat([agg, df])

        agg = agg.resample(rate).sum()
        agg = (agg / len(desks)) * 100
        return agg

    agg_h = aggregate_by(desks, 'H')
    agg_d = aggregate_by(desks, 'D').shift(12, freq='H')

    plt.plot(agg_h, label='Hourly')
    plt.plot(agg_d, 'o-', label='Daily')

    plt.xlabel('Timestamp')
    plt.ylabel('Percentage')
    plt.title('Occupancy')
    plt.legend()
    plt.show()
