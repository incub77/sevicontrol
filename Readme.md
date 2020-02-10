How it works
============
            
 The home ventilation system is controlled via a small surface mounted box, that houses two components. 
 A small control panel, with some buttons to switch modes and a controller board, that basically drives the fans.
 The control panel and the controller board are connected with four wires. 
 The outer two wires provide 12V DC for the board and the fans, while the inner two wires are used by a RS-485 bus.
 To control the home ventilation system, we disconnect the bus and build two busses with a Raspberry Pi in the middle.
     
 
    +--------------------+--------------------+    
    |                    |                    |
    |     Controller     |       Control      |
    |                    |        Panel       |
    |                    |                    |
    |         |          |          |         |
    +--------------------+--------------------+
              |                     |     
              |                     +------+
              +-------------------------+  |
                                        |  |
               +--------------------+   |  | <-- dual wires for RS-485
               |                    |   |  |
               |    RaspberryPi     |==|+  |
               |                    |      |
               |                    |==|---+
               +--------------------+ ^
                                      |
                                   USB-adapter   
I was not able to identify the protocol used on the bus. 
It seems to be a proprietary protocol with an XOR "checksum" at the end of each message. 
The software uses the checksum to check whether a message from the control panel was received properly. The messages
used to control the ventilation system have been captured and are being replayed by the Pi to now control the system.
There are four messages being send by the control panel, that seem to have no effect on the system. They are probably 
meant to query sensors, that are not present in my installation. These messages are passed through by the software.     
      

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
5. Copy nginx config  
`sudo cp ./etc/nginx/nginx.conf /etc/nginx/`  
6. Setup tmp files  
`sudo cp ./etc/tmpfiles.d/* /etc/tmpfiles.d/`
7. Register systemd services  
`sudo cp ./etc/systemd/system/* /etc/systemd/system/`  
`sudo systemctl enable sevi-control`
8. Edit config.yaml to match your settings  
`sudo cp config.yaml.example config.yaml`  
`sudo vi config.yaml`  
9. Create system user & group  
`sudo addgroup --system sevictl`  
`sudo adduser --system --home /home/sevicontrol/ --no-create-home --ingroup sevictl sevictl`  
10. Change owner  
`sudo chown sevictl:sevictl -R /home/sevicontrol`
11. Restart  
`sudo shutdown -r now`


