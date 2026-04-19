# **READ ME - SETTING UP OTP CAPTCHA ANCHOR.**



**This script is for**

**educational purposes only**



## Pre-requirements



\* VPS (UBUNTU OR DEBIAN 4GB TO 6GB)

\* CLEAN DOMAIN, CATEGORIZE YOUR DOMAIN AT FORTIGUARD OR WHOM YOU CHOOSE.

\* Infobip Email Token Infobip.com (its free and cheap)



SSH INTO YOUR VPS.

ssh root@127.0.0.0.0.1

password

🧱 1. Update system

sudo apt update && sudo apt upgrade -y

🧰 2. Install required packages

sudo apt install apache2 python3 python3-venv python3-pip -y

--- Enable Apache modules:

sudo a2enmod proxy proxy_http rewrite
sudo systemctl restart apache2

📁 3. Create project structure

sudo mkdir -p /var/www/otp/
sudo mkdir -p /var/www/otp/static
sudo mkdir -p /var/www/otp/static/api (copy index.html file for otp page into this director)
sudo mkdir -p /var/www/otp/static/dashboard (copy index.htm of dashboards directory to frontend www)
sudo mkdir -p /var/www/otp/backend (copy api.py into this director)
sudo chown -R $USER:$USER /var/www/otp

📄 4. Upload your files

git clone https://github.com/craig-morris/otp_anchor_redirect.git
cd otp_anchor_redirect
sudo cp otp_anchor_redirect/api/index.html /var/www/otp/static/api/
sudo cp otp_anchor_redirect/dashboard/index.html /var/www/otp/static/dashboard/

sudo chown www-data:www-data /var/www/otp/static/api/index.html
sudo chown www-data:www-data /var/www/otp/static/dashboard/index.html




sudo a2enmod proxy

sudo a2enmod proxy\_http

sudo a2enmod proxy\_balancer

sudo a2enmod lbmethod\_byrequests

sudo a2enmod env

sudo a2enmod include

sudo a2enmod setenvif

sudo a2enmod ssl

sudo a2ensite default-ssl

sudo a2enmod cache

sudo a2enmod substitute

sudo a2enmod headers

sudo a2enmod rewrite

sudo a2dismod access\_compat





sudo systemctl start apache2





sudo systemctl enable apache2





sudo apt -y install git





## Install Curl and Python (Do not Use pip)



sudo apt update

sudo apt install python3

python3 --version



sudo apt install curl

curl --version



## Mostcases you might need to install Flask, we will be using it to build or Application.



Pull/fork repository from GitHub: 





sudo mkdir /var/otp/api

sudo mkdir /var/otp/primary





sudo cp -r ./static/api/ /var/otp/



sudo cp -r ./static/primary/ /var/otp/



## Check out Apps and Scripts to edit your app.py file and add your own API and token to send emails.

## Go to Api.html to change your url/links.

## 

## Go to /etc/hosts to edit your hosts, Also edit your apache2 file and also your vhost file so it points to your external domain. edit 000-default.conf file if you have it.





## Installing your Letscrypt SSL after coming page is up and running (live)





sudo apt update

sudo apt install snapd

sudo snap install --classic certbot

ln -s /snap/bin/certbot /usr/bin/certbot

sudo certbot --apache

sudo certbot renew --dry-run



## Installing your Letscrypt SSL after coming page is up and running (live)
**Check out : www.ogtoolstore.de**

\------------------------------------------------------------------------------------------------------

Remember to update your Turnstile site key in /api/index.html
Remember to update your Turnstile secret key in /backend/app.py

Remember to update your infobip sending apikey in /backend/app.py
INFOBIP_HOST = os.getenv("INFOBIP_HOST", "---")
INFOBIP_API_KEY = os.getenv("INFOBIP_API_KEY", "---")
INFOBIP_SENDER = os.getenv("INFOBIP_SENDER", "---")

For testing and debugging visit Infobip.com



Following script was used for debugging: 

curl -X POST https://xxxx.api.infobip.com/email/4/messages \\

&#x20; -H "Content-Type: application/json" \\

&#x20; -d '{"email":"xxxx@xxxx-corp.com"}'









