import argparse
import os
import sys

from svcutils.service import Config, Service

from bodiez import WORK_PATH, NAME
from bodiez.collector import collect


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--path', '-p', default=os.getcwd())
    subparsers = parser.add_subparsers(dest='cmd')
    collect_parser = subparsers.add_parser('collect')
    collect_parser.add_argument('--daemon', action='store_true')
    collect_parser.add_argument('--task', action='store_true')
    collect_parser.add_argument('--interactive', '-i', action='store_true')
    args = parser.parse_args()
    if not args.cmd:
        parser.print_help()
        sys.exit()
    return args


def main():
    args = parse_args()
    path = os.path.realpath(os.path.expanduser(args.path))
    config = Config(
        os.path.join(path, 'user_settings.py'),
        GOOGLE_CREDS=os.path.join(WORK_PATH, 'google_creds.json'),
        FIRESTORE_COLLECTION=NAME,
        HEADLESS=not args.interactive,
        MIN_BODIES_HISTORY=50,
        RUN_DELTA=3600,
    )
    if args.cmd == 'collect':
        service = Service(
            target=collect,
            args=(config,),
            work_path=WORK_PATH,
            run_delta=config.RUN_DELTA,
            force_run_delta=2 * config.RUN_DELTA,
            max_cpu_percent=10,
            min_uptime=300,
            requires_online=True,
        )
        if args.daemon:
            service.run()
        elif args.task:
            service.run_once()
        else:
            collect(config, force=True)


if __name__ == '__main__':
    main()
