Compatibility
=============

This software has been tested with Raspberry Pis 1 B+, Zero WH, 3 B+ and 4 B. For Pi 4 B an [eeprom update](https://www.raspberrypi.org/documentation/hardware/raspberrypi/booteeprom.md) might be necessary.  
As RS-485 adapter I used [this shield](https://www.reichelt.de/raspberry-pi-rs485-interface-rpi-rs485-p162304.html?LANGUAGE=EN) for development and these [USB-adapters](https://www.amazon.de/Converter-Adapter-Arduino-Prototyping-Mikrocontroller/dp/B01MQTKZ6D/) for production. 


Install
=======

I assume you have a brand new Raspbian installed like described on 
[raspberrypi.org](https://www.raspberrypi.org/documentation/installation/installing-images/README.md).

1. Install needed Raspbian packages  
`sudo apt install nginx python3-pip python3-serial gunicorn3 git`
2. Copy SeviControl to Pi  
`cd /home`  
`sudo git clone https://github.com/incub77/sevicontrol.git`
3. Install Python dependencies  
`cd /home/sevicontrol`  
`sudo pip3 install -r requirements.txt`
4. Allow none priviliged users access to USB ports    
`cd provisioning`  
`sudo cp ./etc/udev/rules.d/50-sevicontrol-usb.rules /etc/udev/rules.d/`
5. Register systemd service  
`sudo cp ./etc/systemd/system/* /etc/systemd/system/`  
`sudo systemctl enable sevi-control`
6. Setup tmp files  
`sudo cp ./etc/tmpfiles.d/* /etc/tmpfiles.d/`  
7. Change owner  
`sudo chown nobody:nogroup -R /home/sevicontrol`
8. Edit config.yaml to match your settings  
`sudo vi config.yaml`  
9. Restart  
`sudo shutdown -r now`


