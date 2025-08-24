import argparse
import os
import sys

from svcutils.service import Config, Service


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--path', '-p', default=os.getcwd())
    parser.add_argument('--headful', action='store_true')
    subparsers = parser.add_subparsers(dest='cmd')
    collect_parser = subparsers.add_parser('collect')
    collect_parser.add_argument('--daemon', action='store_true')
    collect_parser.add_argument('--task', action='store_true')
    test_parser = subparsers.add_parser('test')
    test_parser.add_argument('--id')
    args = parser.parse_args()
    if not args.cmd:
        parser.print_help()
        sys.exit()
    return args


def wrap_collect(*args, **kwargs):
    from bodiez import collector
    return collector.collect(*args, **kwargs)


def main():
    from bodiez import WORK_DIR
    args = parse_args()
    path = os.path.realpath(os.path.expanduser(args.path))
    config = Config(
        os.path.join(path, 'user_settings.py'),
        STATE_DIR=os.path.join(WORK_DIR, 'state'),
        STORE_DIR=os.path.join(path, 'store'),
        HEADLESS=not args.headful,
        RUN_DELTA=3600,
    )
    if args.cmd == 'collect':
        service = Service(
            target=wrap_collect,
            args=(config,),
            work_dir=WORK_DIR,
            run_delta=config.RUN_DELTA,
            min_uptime=180,
            requires_online=True,
        )
        if args.daemon:
            service.run()
        elif args.task:
            service.run_once()
        else:
            wrap_collect(config, force=True)
    elif args.cmd == 'test':
        from bodiez import collector
        collector.test(config, url_id=args.id)


if __name__ == '__main__':
    main()
