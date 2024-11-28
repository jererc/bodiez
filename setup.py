from setuptools import setup, find_packages
from setuptools.command.install import install
import subprocess
import sys


class CustomInstallCommand(install):
    """Customized setuptools install command to run `playwright install`."""
    def run(self):
        # Run the standard install process
        install.run(self)

        # Run `playwright install` using the Python executable
        try:
            subprocess.check_call([sys.executable, '-m', 'playwright', 'install'])
        except subprocess.CalledProcessError as e:
            print(f"Failed to run `playwright install`: {e}")
            sys.exit(1)


setup(
    name='bodiez',
    version='2024.11.27.182846',
    author='jererc',
    author_email='jererc@gmail.com',
    url='https://github.com/jererc/bodiez',
    packages=find_packages(exclude=['tests*']),
    python_requires='>=3.10',
    install_requires=[
        'playwright',
        # 'svcutils @ git+https://github.com/jererc/svcutils.git@main#egg=svcutils',
        'svcutils @ https://github.com/jererc/svcutils/archive/refs/heads/main.zip',
    ],
    cmdclass={
        'install': CustomInstallCommand,
    },
    extras_require={
        'dev': ['flake8', 'pytest'],
    },
    entry_points={
        'console_scripts': [
            'bodiez=bodiez.main:main',
        ],
    },
    include_package_data=True,
)
