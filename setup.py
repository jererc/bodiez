from setuptools import setup, find_packages

setup(
    name='bodiez',
    version='2024.12.02.181759',
    author='jererc',
    author_email='jererc@gmail.com',
    url='https://github.com/jererc/bodiez',
    packages=find_packages(exclude=['tests*']),
    python_requires='>=3.10',
    install_requires=[
        'google-cloud-firestore',
        'playwright',
        # 'svcutils @ git+https://github.com/jererc/svcutils.git@main#egg=svcutils',
        'svcutils @ https://github.com/jererc/svcutils/archive/refs/heads/main.zip',
    ],
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
