# FoodCatalog
Project: Linux Server of the Food Catalog
Author: Rosalie Thobe


IP Address: 34.201.6.151
Server name: ec2-34-201-6-151.compute-1.amazonaws.com 
	(that is what it told me when I used nslookup)

Software installed:
  I updated all of the packages by: sudo apt-get upgrade
  I also installed: python, Flask-SQLAlchemy, flask, pip, sqlalchemy, flask-seasurf,
upgraded oauth2client, virtualenv, apache2, postgresql

Description:
   Task was to set up our previous food catalog on a server.
  I used AWS Lightsail
to actually get the server.  This project was supposed to teach us how to
ssh onto the server with keys and with different permissions and users.
   Overall, this project was rather complicated.  Lots of little items that needed
to be done in order to actually complete the project.

Configurations:
   - I updated all of the packages
   - Created user: grader
   - gave grader sudo access by: grader  ALL=(ALL:ALL) ALL
   - Created grader's private ssh key
   - Put key onto server and gave key a chmod of 644
   - Configured the firewall to allow only 2200, www, 123, and 80 ports
   - Changed the time zone so that it was UTC
   - Installed postgres and created database. Gave access to Owner
   - Set up the virtual environment and gave that a permission of 777

Outside Resources used:
  https://www.digitalocean.com/community/tutorials/how-to-set-up-a-firewall-with-ufw-on-ubuntu-18-04
  Udacity Forum - Student Hub
  Udacity Lessons about the Linux server
  https://www.digitalocean.com/community/tutorials/how-to-deploy-a-flask-application-on-an-ubuntu-vps
  
