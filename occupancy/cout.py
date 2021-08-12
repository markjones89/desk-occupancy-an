N = '    '


def config(args):
    print('config:')

    # API authentication details.
    if args.sample:
        print(f'{N}using sample data')
    else:
        print(f'{N}project: {args.project_id}')
        print(f'{N}label:   {args.label}')
        print(f'{N}days:    {args.days}')


def missing_credentials(args):
    print('\nMissing credentials:')
    print(f'{N}key_id:  {args.key_id}')
    print(f'{N}secret:  {args.secret}')
    print(f'{N}email:   {args.email}')
    print(f'{N}project: {args.project_id}')
    print('\nTips:')
    print('Use the --sample flag for provided sample data.')
    print('Use the --plot-agg and/or --plot-desks flags for plotting.')
    print('\nExiting...\n')


def device_events(device_id, n):
    print(f'{device_id:<23} {n:>7}')
