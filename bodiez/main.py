import argparse
import os
import sys

from svcutils.service import Config, Service

from bodiez import WORK_DIR, NAME, collector


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--path', '-p', default=os.getcwd())
    subparsers = parser.add_subparsers(dest='cmd')
    collect_parser = subparsers.add_parser('collect')
    collect_parser.add_argument('--headful', action='store_true')
    collect_parser.add_argument('--daemon', action='store_true')
    collect_parser.add_argument('--task', action='store_true')
    test_parser = subparsers.add_parser('test')
    test_parser.add_argument('--headful', action='store_true')
    test_parser.add_argument('--id')
    test_parser.add_argument('--login-timeout', type=int, default=0)
    args = parser.parse_args()
    if not args.cmd:
        parser.print_help()
        sys.exit()
    return args


def main():
    args = parse_args()
    path = os.path.realpath(os.path.expanduser(args.path))
    login_timeout = getattr(args, 'login_timeout', 0)
    config = Config(
        os.path.join(path, 'user_settings.py'),
        SHARED_STORE_DIR=os.path.join(path, 'store'),
        GOOGLE_CREDS=os.path.join(WORK_DIR, 'google_creds.json'),
        FIRESTORE_COLLECTION=NAME,
        HEADLESS=not (args.headful or login_timeout),
        LOGIN_TIMEOUT=login_timeout,
        MIN_BODIES_HISTORY=50,
        RUN_DELTA=3600,
    )
    if args.cmd == 'collect':
        service = Service(
            target=collector.collect,
            args=(config,),
            work_dir=WORK_DIR,
            run_delta=config.RUN_DELTA,
            force_run_delta=2 * config.RUN_DELTA,
            max_cpu_percent=10,
            min_uptime=180,
            requires_online=True,
        )
        if args.daemon:
            service.run()
        elif args.task:
            service.run_once()
        else:
            collector.collect(config, force=True)
    elif args.cmd == 'test':
        collector.test(config, url_id=args.id)


if __name__ == '__main__':
    main()
