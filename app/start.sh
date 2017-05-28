#!/bin/bash

#pHAT DAC (removes default audio)
if [[ "$PHAT_DAC" = "1" ]]; then
  rmmod snd_bcm2835 || true
fi

# Handle Kodi userdata folder, /data is a permanent folder between containers
mkdir /data/kodi >/dev/null 2>&1 || true && rm -rf /root/.kodi && ln -s /data/kodi /root/.kodi
mkdir /data/Pictures >/dev/null 2>&1 || true
# cp /usr/src/app/test.jpg /data/Pictures

cp /usr/src/app/autoexec.py /data/kodi/userdata
cp /usr/src/app/guisettings.xml /data/kodi/userdata/

# Move plugin.dbmc
mkdir /data/kodi/addons/plugin.dbmc >/dev/null 2>&1 || true
cp -r /usr/src/app/plugin.dbmc/* /data/kodi/addons/plugin.dbmc

mkdir /data/kodi/userdata/addon_data/plugin.dbmc >/dev/null 2>&1 || true
cp -r /usr/src/app/plugin.dbmc.addon_data/* /data/kodi/userdata/addon_data/plugin.dbmc

# Move script.service.kodi.callbacks
mkdir /data/kodi/addons/script.service.kodi.callbacks >/dev/null 2>&1 || true
cp -r /usr/src/app/script.service.kodi.callbacks/* /data/kodi/addons/script.service.kodi.callbacks

mkdir /data/kodi/userdata/addon_data/script.service.kodi.callbacks >/dev/null 2>&1 || true
cp -r /usr/src/app/script.service.kodi.callbacks.addon_data/* /data/kodi/userdata/addon_data/script.service.kodi.callbacks

# Use sed here to insert environment var with plugin token
echo "Using Dropbox: $DBX_FOLDER"
sed -i "36s|.*V/.*|V/$DBX_FOLDER|" '/data/kodi/userdata/addon_data/plugin.dbmc/accounts/Superliminal Dropbox/settings'

echo "Display effects: $EFFECTS"

echo "TEST: $RESIN_HOST_CONFIG_gpu_mem"

# Insert slideshow stay time
sed -i "s|.*<staytime.*|<staytime default='true'>$STAYTIME</staytime>|" '/data/kodi/userdata/guisettings.xml'
sed -i "s|.*<webserver.*|<webserver>$WEBSRV</webserver>|" '/data/kodi/userdata/guisettings.xml'
sed -i "s|.*<webserverpassword.*|<webserverpassword>$WEB_PASS</webserverpassword>|" '/data/kodi/userdata/guisettings.xml'
sed -i "s|.*<webserverusername.*|<webserverusername>$WEB_USR</webserverusername>|" '/data/kodi/userdata/guisettings.xml'
sed -i "s|.*<webserverport.*|<webserverport default='true'>$WEB_PORT</webserverport>|" '/data/kodi/userdata/guisettings.xml'
sed -i "s|.*<shuffle.*|<shuffle>$SHUFFLE</shuffle>|" '/data/kodi/userdata/guisettings.xml'
sed -i "s|.*<displayeffects.*|<displayeffects default='false'>$EFFECTS</displayeffects>|" '/data/kodi/userdata/guisettings.xml'

# python /usr/src/app/startup.py #Only handles USB

# ln -s /data/kodi/addons/plugin.dbmc /usr/share/kodi/addons/plugin.dbmc
# ln -s /data/kodi/addons/script.service.kodi.callbacks /usr/share/kodi/addons/script.service.kodi.callbacks
cp /usr/src/app/addon-manifest.xml /usr/share/kodi/system

while true; do
    DBUS_SYSTEM_BUS_ADDRESS=unix:path=/host_run/dbus/system_bus_socket /usr/bin/kodi-standalone
done
