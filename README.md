# Anycubic Cloud API [BETA IN PRODUCTION]
Cloud API and web server to control Anycubic Cloud server
Anycubic has been quite slack in creating a cloud server that you can control online. They have an app that you can use to start prints and see status of prints and print files etc. But it does not work on a PC nor does it allow uploading of files without the Anycubic software which is also quite limited.

I decided to reverse engineer the android / IOS app to get the API calls as well as the Anycubic slicer software which allows uploading of GCODE files to your cloud account. I put all of this into a web server using Python Django.

The features so far include:
- See print files uploaded and their specific information (Deleting files is not yet supported as I have not been able to reverse engineer this)
- Start prints and select the specific printer attached to your anycubic cloud account to print to
- See printers and their status / information
- See current job information, status and time remaining
- See previous prints and times and information
- Upload new print files to the cloud in PWMB format ready to print

Please note this is still quite new and IN PRODUCTION. There will probably be issues and teething problems. I have uploaded this for anyone that might be interested and I am stil producing it. It is NOT READY FOR PRODUCTION and you will probably need to know and understand some basic Python Django setup instructions to get this running.

The program consists of a Python API module that I created that contains most of the REST API calls to control the Anycubic Cloud API which Python Django uses to speak to the system. The API module is a basic dump of the API calls which I am still working through and will continue to update as I understand more of them.

The web server has a testing button and dialog that can be used to test some of the calls which have not yet been set up.

Installation:

To install you will need Python3 preferably set up in a virtual environment.
Follow these steps in the folder you would like to install the server

    sudo apt install -y git python3 python3-dev python3-virtualenv python-dbus libdbus-1-dev libglib2.0-dev
    virtualenv anycubic_cloud
    cd anycubic_cloud
    source bin/activate
    python3 -m pip install --upgrade pip
    pip3 install django django-crispy-forms requests pyyaml desktop-notifier
    mkdir src
    cd src
    git clone https://github.com/Royrdan/anycubic_cloud
    mv anycubic_cloud anycubic_cloud_repo
    django-admin startproject anycubic_cloud
    SECRET_KEY=$(grep -h "SECRET_KEY" anycubic_cloud/anycubic_cloud/settings.py | sed 's/.* = //')
    cp -r anycubic_cloud_repo/* anycubic_cloud
    rm -rf anycubic_cloud_repo
    sed -i "s/SECRET_KEY = <SECRET_KEY_HERE>/# SECRET_KEY = <see bottom of file>/" anycubic_cloud/anycubic_cloud/settings.py
    echo "SECRET_KEY = $SECRET_KEY" >> anycubic_cloud/anycubic_cloud/settings.py
    anycubic_cloud/manage.py migrate
    anycubic_cloud/manage.py runserver

The server should be running and go to localhost:8000 in your web browser. Login to your anycubic account and everything should be setup.

Please let me know if I have any mistakes with the instructions as I have done them out of memory. There may have been something I forgot or missed. Thanks
Also please let me know any improvements / issues.
If you can figure out the delete command let me know.
