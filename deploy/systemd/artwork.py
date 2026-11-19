#!/usr/bin/python3
"""Start the installed kiosk through its approved systemd seat/session."""
import argparse
import os
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('start',), help='Start thirsty.service (requires sudo)')
    parser.parse_args()
    command = ['/usr/bin/systemctl', 'start', 'thirsty.service']
    if os.geteuid() != 0:
        command = ['/usr/bin/sudo', '--', *command]
    os.execv(command[0], command)


if __name__ == '__main__':
    try:
        main()
    except OSError as exc:
        print(f'Artwork start failed: {exc}', file=sys.stderr)
        sys.exit(2)
