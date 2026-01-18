import os
import urllib.request

url = 'https://raw.githubusercontent.com/jererc/svcutils/refs/heads/main/svcutils/bootstrap.py'
exec(urllib.request.urlopen(url).read().decode('utf-8'))
Bootstrapper(
    name='bodiez',
    install_requires=[
        # 'git+https://github.com/jererc/bodiez.git',
        'bodiez @ https://github.com/jererc/bodiez/archive/refs/heads/main.zip',
    ],
    force_reinstall=True,
    init_cmds=[
        ['playwright', 'install-deps'],
    ],
    extra_cmds=[
        ['playwright', 'install', 'chromium'],
    ],
    tasks=[
        {'name': 'bodiez', 'args': ['bodiez.main', '-p', os.getcwd(), 'collect', '--task']},
    ],
    download_assets=[
        {'filename': 'user_settings.py', 'url': 'https://raw.githubusercontent.com/jererc/bodiez/refs/heads/main/bootstrap/user_settings.py'},
    ],
)