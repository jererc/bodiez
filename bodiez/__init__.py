from svcutils.service import get_logger, get_work_dir

NAME = 'bodiez'
WORK_DIR = get_work_dir(NAME)
logger = get_logger(path=WORK_DIR, name=NAME)
