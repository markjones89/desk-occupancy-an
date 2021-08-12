import sys
import argparse

from occupancy import cout


def parse_sysargs():

    parser = argparse.ArgumentParser(
        description='Desk Occupancy Application Note',
    )
    parser.add_argument(
        '--key-id',
        metavar='',
        type=str,
        help='Service Account Key ID',
        required=False,
    )
    parser.add_argument(
        '--secret',
        metavar='',
        type=str,
        help='Service Account Secret',
        required=False,
    )
    parser.add_argument(
        '--email',
        metavar='',
        type=str,
        help='Service Account Email',
        required=False,
    )
    parser.add_argument(
        '--project-id',
        metavar='',
        type=str,
        help='Identifier of project where devices are held.',
        required=False,
    )
    parser.add_argument(
        '--label',
        metavar='',
        type=str,
        help='Only fetches sensors with provided label key.',
        required=False,
    )
    parser.add_argument(
        '--days',
        metavar='',
        type=int,
        help='Days of event history to fetch.',
        default=7,
    )
    parser.add_argument(
        '--sample',
        help='Use provided sample data.',
        action='store_true',
    )
    parser.add_argument(
        '--plot-desks',
        help='Plot each individual desk results.',
        action='store_true',
    )
    parser.add_argument(
        '--plot-agg',
        help='Plot aggregated results.',
        action='store_true',
    )
    args = parser.parse_args()

    sanitize_credentials(args)

    return args


def sanitize_credentials(args):
    # If sample is set, do nothing.
    if args.sample:
        return

    # If None in credentials, end execution.
    if None in [args.key_id, args.secret, args.email, args.project_id]:
        cout.missing_credentials(args)
        sys.exit()
