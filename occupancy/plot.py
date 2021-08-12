import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.transforms as mtransforms


def single(desk):
    trig = np.array(desk.state_array)
    _, ax = plt.subplots()
    ax.plot(desk.timestamps, desk.celsius, label='Raw Temperature')
    trans = mtransforms.blended_transform_factory(ax.transData, ax.transAxes)
    ax.fill_between(
        np.array(desk.timestamps),
        0, 1,
        where=trig,
        transform=trans,
        color='C0', alpha=0.25,
        label='Occupied',
    )
    plt.ylabel('Celsius')
    plt.xlabel('Timestamp')
    plt.legend()
    plt.show()


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
    plt.plot(agg_d, linewidth=3, label='Daily')

    plt.xlabel('Timestamp')
    plt.ylabel('Occupancy [%]')
    plt.title('Occupancy')
    plt.legend()
    plt.show()
