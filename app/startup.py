# Superliminal-OSMC autoexec.py script
# Scott Chase Waggener
# 5/6/17

# HOW TO USE

# 1) Burn an image of Superliminal and leave the SD card in your computer
# 2) Open the SD card folder in windows
# 3) Copy the configuration files
#   a) File 'settings' that configures Dropbox
#   b) File 'wpa_suppicant.conf' that configures Wifi
#   c) File 'hosts' that sets the hostname (/etc/hosts)



# This script is placed in '/home/pi' and is run at launch using Raspbian systemd
# See http://kodi.wiki/view/Add-on:Dbmc%20(Dropbox%20add-on)#Caching_or_streaming_media
#   for information on how photos are stored within osmc

# Photos are cached to a folder
#   This folder, and the specific dropbox folder to fetch from are stored in a settings files
#   '/home/pi/.kodi/userdata/addon_data/plugin.dbmc/Superliminal Dropbox/settings'

import os.path
import subprocess
import shutil
import os
from sh import mount
from sh import umount
import re
import time

slideshow_path = "/data/Pictures"
dbmc_settings_dest = "/home/pi/.kodi/userdata/addon_data/plugin.dbmc/accounts/Superliminal Dropbox/settings"
dbmc_dir = "/home/pi/.kodi/userdata/addon_data/plugin.dbmc/accounts/Superliminal Dropbox/"
img_types = [".jpg",".png",".jpeg",".gif",".tiff",".bmp","mp4","avi"]

# Check for hosts or settings file in /boot, if exists move to where they need to go
settings_path = "/boot/settings"
hosts_path = "/boot/hostname"

# Take some manual control over plymouth splash screen
def plymouth_start():
    subprocess.call(["systemctl", "stop", "plymouth-quit.service"])
    subprocess.call("plymouthd")
    subprocess.call(["plymouth","show-splash"])

def plymouth_stop():
    subprocess.call(["plymouth","quit","--retain-splash"])
    subprocess.call(["plymouth","--wait"])

# Prints status message to plymouth boot screen
def plymouth_print(text):
    subprocess.call(["plymouth","message","--text="+text])

# Returns the IP address of the Pi
def get_IP():
    ip = subprocess.check_output(["hostname","-I"]).rstrip("\n\r")
    if len(ip) > 4 :
        return ip
    else:
        return "USB"

# Returns the hostname of the Pi, or "USB" if not connected to a network
def get_hostname():
    if len(get_IP()) < 4 :
        return "USB"
    else:
        return subprocess.check_output(["tail","/etc/hostname"]).rstrip("\n\r")

# Returns true if a wlan interface exists, or false otherwise
def check_wlan_dev():
    try:
        devs = subprocess.check_output(["iw","dev"])
    except:
        return False
    devs_re = re.compile("\tInterface +(?P<lan>\w+)", re.I)
    for i in devs.split('\n'):
        if i:
            info = devs_re.match(i)
            if info:
                dinfo = info.groupdict()
                dinfo = dinfo.pop('lan')
                print "Found a network interface"
                return True
    print "No network interfaces, must be USB"
    return False

# Launches Kodi
def start_kodi():
    plymouth_print("Starting Kodi...")

    if not os.path.isdir(slideshow_path):
        print("Pictures folder doesn't exist, creating it now")
        os.makedirs(slideshow_path)

    files = len(os.walk(slideshow_path).next()[2])
    ip = get_IP()
    hostname = get_hostname()

    if not os.path.exists(dbmc_settings_dest):
        print("Error: No Dropbox configuration. Proceeding")
        count = 0
        while count < 10 :
            plymouth_print("No Dropbox configuration"+"\r\nStarting slideshow in "+str(10-count)+"s...")
            time.sleep(1)
            count += 1
        plymouth_print("Starting slideshow")
        subprocess.call(["sudo","-u","pi","kodi"])
        print("Kodi started")
        return;

    dropbox = subprocess.check_output(["tail",dbmc_settings_dest])
    dropbox_re = re.compile("V/+(?P<folder>\w+)", re.I)
    dropbox_folder = []
    for i in dropbox.split('\n'):
        if i:
            info = dropbox_re.match(i)
            if info:
                dinfo = info.groupdict()
                dinfo = dinfo.pop('folder')
                dropbox_folder.append(dinfo)
    print "IP: "+ip

    print "DBX: "
    print dropbox_folder

    print "Hostname: "+hostname
    print dropbox_folder[0]+" - "+str(files)+" Flyers"

    rssi = get_RSSI()
    if not rssi:
        rssi = "No WiFi"
    else:
        rssi = str(rssi)+"%"
    status_string = dropbox_folder[0]+" - "+str(files)+" Flyers\r\n"+ip+" - "+rssi

    count = 0
    while count < 10 :
        plymouth_print(status_string+"\r\nStarting slideshow in "+str(10-count)+"s...")
        time.sleep(1)
        count += 1

    plymouth_print("Starting slideshow")
    subprocess.call(["sudo","-u","pi","kodi"])
    print("Kodi started")
    plymouth_stop()

def clean_pictures():
    shutil.rmtree(slideshow_path)
    os.mkdir(slideshow_path)
    os.chmod(slideshow_path,0755)
    os.chown(slideshow_path,1000,1000)  # UID of user 'pi'
    shutil.move(dbmc_dir+"sync_data.pik",dbmc_dir+"sync_data.bak.pik")

# Copies all files from USB stick to /home/pi/Pictures
# If no USB found, proceeds forward and waits for the network
def usb_download():
    # Get a list of all /dev/sd* partitions
    usb_partitions_re = re.compile("/dev/sd+(?P<part>\w+)", re.I)
    partitions = subprocess.check_output(["fdisk","-l"])
    devices = []
    for i in partitions.split('\n'):
        if i:
            info = usb_partitions_re.match(i)
            if info:
                dinfo = info.groupdict()
                dinfo = '/dev/sd%s' % (dinfo.pop('part'))
                devices.append(dinfo)
    print devices

    # If no USB drives, return and try calling internet_wait()
    if not len(devices):
        return

    # Delete local pictures, make sure no USB is mounted before we begin
    clean_pictures()
    try:
        umount("/mnt")
    except:
        pass

    # For each partition, look for image files on the partition
    for i in devices:
        mount(i,"/mnt")
        file_list = subprocess.check_output(["ls","/mnt"])

        for i in file_list.split('\n'):
            if i.lower().endswith(tuple(img_types)):
                shutil.copy("/mnt/"+i,"/home/pi/Pictures")
        umount("/mnt")

    # Recursively chown/chmod Pictures folder
    for root, dirs, files in os.walk(slideshow_path):
        for f in files:
            os.chmod( os.path.join(slideshow_path,f), 0644 )
            os.chown( os.path.join(slideshow_path,f), 1000, 1000 )  # UID of user 'pi'


# Looks for DBMC settings file in /boot, copies it to adddon folder if exists
def check_settings_files():
    if os.path.isfile(hosts_path) :
        shutil.copy(hosts_path,"/etc/hostname")
        shutil.move(hosts_path,hosts_path+".old")
        print("Moved /etc/hostname")
    else :
        print("No hosts file found")

    if os.path.isfile(settings_path) :
        # First move the settings file, set permissions to 755
        shutil.copy(settings_path,dbmc_settings_dest)
        shutil.move(settings_path,settings_path+".old")
        os.chmod(dbmc_settings_dest,0755)

        clean_pictures()

        print("Moved DBMC settings file")
    else:
        print("No DBMC settings file found")

# Returns the RSSI in x/100
def get_RSSI():
    try :
        rssi = subprocess.check_output(["iw","dev","wlan0","link"])
    except:
        return 0

    rssi_re = re.compile("\tsignal: -+(?P<rssi>\w+)", re.I)
    for i in rssi.split('\n'):
        if i:
            info = rssi_re.match(i)
            if info:
                dinfo = info.groupdict()
                dinfo = dinfo.pop('rssi')
                if int(dinfo) >= 100 :
                    quality = 0
                elif int(dinfo) <= 50 :
                    quality = 100
                else:
                    quality = -2 * (int(dinfo) - 100)
                return quality

# Waits for the network to come up with countdown
def internet_wait():
    plymouth_print("No USB, waiting 30s for network...")
    ip = ""
    count = 0
    while len(ip) < 4 and count < 30:
        plymouth_print("No USB, waiting "+str(30-count)+"s for network...")
        ip = get_IP()
        time.sleep(1)
        count += 1

def main():
    # check_settings_files()
    usb_download()

main()
