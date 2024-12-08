#!/bin/bash
pyinstaller --onefile --name bodiez bodiez/main.py

# pyinstaller --onefile --name bodiez \
#   --add-binary /usr/lib/x86_64-linux-gnu/libvpx.so.7:. \
#   --add-binary /usr/lib/x86_64-linux-gnu/libavif.so.13:. \
#   --add-binary /usr/lib/x86_64-linux-gnu/libicudata.so.70:. \
#   bodiez/main.py

