Need to install
------------------
arrow
CherryPy
RPi.GPIO
MarkupSafe
psutil


Note: pip was not working so I installed manualy (ie wget, unzip, cd, python3 setup.py instll)

Also setup a ntp server as software records time when power off was triggered


Configuration things: 

Using raspi-config

time zone: 'America/Los_Angeles'

Added 

ExecStartPre=/bin/mkdir /var/log/nginx

To the nginx unit-file


