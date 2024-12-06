Bodiez
======


Install
-------

Download `bootstrap\bootstrap.bat` or `bootstrap\bootstrap.sh` in some directory and run it.
A windows task / linux crontab is created.
Set the `URLS` and params in the `user_settings.py` config file.


DB
--

For google firestore: create a google cloud project, enable firestore, create the default db, download the service credentials to `~/.bodiez/google_creds.json`.

Otherwise the data is stored locally and can be shared between hosts using any cloud sync (MEGA, OneDrive, Google Drive, etc).


Testing urls
------------

In a terminal:

```
jererc@ub2404:~$ source ~/venv/bodiez/bin/activate
```

Help:

```
(bodiez) jererc@ub2404:~$ bodiez collect --help
usage: bodiez collect [-h] [--url-id URL_ID] [--daemon] [--task] [--interactive] [--test]

options:
  -h, --help         show this help message and exit
  --url-id URL_ID
  --daemon
  --task
  --interactive, -i
  --test
```

In the `user_settings.py` dir:

```
(bodiez) jererc@ub2404:~/tmp/test-bodiez$ bodiez collect --test --interactive --url-id games
WARNING:svcutils.service:/home/jererc/.bodiez/google_creds.json does not exist, using local storage /home/jererc/tmp/test-bodiez/bodiez
DEBUG:svcutils.service:processing games
DEBUG:svcutils.service:collected bodies for games with parser simple_element:
[
    "Priest Simulator Vampire Show-TENOKE",
    "Uncle Chop's Rocket Shop v1.0.4.5759",
    "Frostpunk.2.Deluxe.Edition.v1.2.1.REPACK-KaOs",
    "Fossilfuel.2.v1.2.4.REPACK-KaOs",
    "theHunter.Call.of.the.Wild.Salzwiesen.Park.REPACK-KaOs",
    "Skydance's BEHEMOTH",
    "World War Z Sin City Apocalypse-RUNE",
    "Touhou Danmaku Kagura Phantasia Lost Digital Deluxe Edition Update v1 5 1 incl D...",
    "The Thing Remastered-SKIDROW",
    "Slopecrashers-TENOKE",
    "River City Girls 2 Double Dragon-TENOKE",
    "Quilts and Cats of Calico Update v1 0 98-TENOKE",
    "Kingdom Rush 5 Alliance TD Update v20241204-TENOKE",
    "Keylocker Turn Based Cyberpunk Action Update v20241204-TENOKE",
    "Fort Solis Update v20241204-TENOKE",
    "Entropy Survivors-TENOKE",
    "DREAMERS-TENOKE",
    "Beach Invasion 1945 Pacific-TENOKE",
    "Spirit Mancer: Demon Hunter Edition (+ 5 DLCs/Bonuses, MULTi9) [FitGirl Repack, ...",
    "I Am Cat"
]
INFO:svcutils.service:collected 20 bodies for games in 7.75 seconds
INFO:svcutils.service:processed in 7.86 seconds
```
