Install
=======

I assume you have a brand new Raspbian installed like described on 
[raspberrypi.org](https://www.raspberrypi.org/documentation/installation/installing-images/README.md).

1. Install needed Raspbian packages  
`sudo apt install nginx python3-pip python3-serial gunicorn3 git`
2. Copy SeviControl to Pi  
`cd /home`  
`git clone https://github.com/incub77/sevicontrol.git`
3. Install Python dependencies  
`cd /home/sevicontrol`  
`sudo pip3 install -r requirements.txt`
4. Allow none priviliged users access to USB ports    
`cd provisioning`  
`sudo cp ./etc/udev/rules.d/50-sevicontrol-usb.rules /etc/udev/rules.d/`
5. Register and start systemd service  
`sudo cp ./etc/systemd/system/* /etc/systemd/system/`  
`sudo systemctl enable sevi-control`
6. Setup tmp files  
`sudo cp ./etc/tmpfiles.d/* /etc/tmpfiles.d/`  
7. Change owner  
`sudo chown nobody:nogroup -R /home/sevicontrol`  


