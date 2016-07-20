#!/bin/bash
ssh mhs-deploy '
ssh auth "
cd /var/www/meerkat_auth;
sudo git checkout master;
sudo git stash;
sudo git pull;
sudo stop uwsgi-auth;
sudo start uwsgi-auth" '
