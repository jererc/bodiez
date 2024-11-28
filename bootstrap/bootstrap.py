import os
import urllib.request

url = 'https://raw.githubusercontent.com/jererc/svcutils/refs/heads/main/svcutils/bootstrap.py'
exec(urllib.request.urlopen(url).read().decode('utf-8'))
Bootstrapper(
    name='bodiez',
    cmd_args=['bodiez.main', '-p', os.getcwd(), 'collect', '--task'],
    install_requires=[
        # 'git+https://github.com/jererc/bodiez.git',
        'bodiez @ https://github.com/jererc/bodiez/archive/refs/heads/main.zip',
    ],
    extra_cmds=[
        ['-m', 'playwright', 'install'],
    ]
    force_reinstall=True,
).setup_task()
