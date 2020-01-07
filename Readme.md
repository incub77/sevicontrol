Install
=======

I assume you have a brand new Raspbian installed like described on 
[raspberrypi.org](https://www.raspberrypi.org/documentation/installation/installing-images/README.md).

1. Install needed Raspbian packages  
`sudo apt install nginx python3-pip python3-serial gunicorn3`
2. Copy SeviControl to Pi  
`sudo mkdir /home/sevictl`  
`scp * dfsdfsdf`
3. Install Python dependencies  
`sudo pip3 install -r requirements.txt`
4. Allow none priviliged users access to USB ports  
`cd provisioning`  
`sudo cp ./etc/udev/rules.d/50-sevictl-usb.rules /etc/udev/rules.d/`
5. Register and start systemd service  
`sudo cp ./etc/systemd/system/* /etc/systemd/system/`  
`sudo systemclt enable sevi-control`
6. Setup tmp files  
`sudo cp ./etc/tmpfile.d/* /etc/tmpfiles.d/`  
7. Change owner  
`sudo chown nobody:nogroup -r /home/sevictl`  


