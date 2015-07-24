#!/usr/bin/env bash

sudo apt-get update
sudo apt-get upgrade

sudo apt-get install -y g++ gcc make dkms
sudo apt-get install -y git git-svn
sudo apt-get install -y curl
sudo apt-get install -y tmux emacs

sudo apt-get install -y python
sudo apt-get install -y python-dev
sudo apt-get install -y python-pip
sudo pip install --upgrade pip

#sudo apt-get install libxml2-dev libxslt1-dev
sudo apt-get install -y libnetcdf-dev
sudo apt-get install -y proj
#sudo apt-get install -y proj-bin  # for ubuntu 14.04

sudo pip install numpy==1.8.0
wget http://download.osgeo.org/gdal/1.11.2/gdal-1.11.2.tar.gz
tar xvfz gdal-1.11.2.tar.gz
cd gdal-1.11.2
./configure --with-python --prefix=/usr
make
sudo make install
sudo ldconfig

sudo apt-get install -y python-gdal

cd ..

# # install pyenv / virtualenv
# if [ ! -d "/home/vagrant/.pyenv" ]; then
#     git clone https://github.com/yyuu/pyenv.git /home/vagrant/.pyenv
#     git clone https://github.com/yyuu/pyenv-virtualenv.git /home/vagrant/.pyenv/plugins/pyenv-virtualenv
#     git clone https://github.com/yyuu/pyenv-pip-rehash.git /home/vagrant/.pyenv/plugins/pyenv-pip-rehash
#     mkdir -p /home/vagrant/.pyenv/shims /home/vagrant/.pyenv/versions
#     chown -R vagrant:vagrant /home/vagrant/.pyenv/
# fi
# cd ~
# touch /home/vagrant/.bashrc
# if ! hash pyenv 2>/dev/null; then
#     echo >> /home/vagrant/.bashrc
#     echo export PYENV_ROOT=/home/vagrant/.pyenv >> /home/vagrant/.bashrc
#     echo 'export PATH="$PYENV_ROOT/bin:$PATH"' >> /home/vagrant/.bashrc
#     echo 'eval "$(pyenv init -)"' >> /home/vagrant/.bashrc
#     echo 'eval "$(pyenv virtualenv-init -)"' >> /home/vagrant/.bashrc
# fi

# source /home/vagrant/.bashrc

# Couldn't get the following to work during provisioning (got
# `pyenv: command not found` errors).  So, leaving it to user to do it
# pyenv install 2.7.8
# pyenv virtualenv 2.7.8 bluesky-2.7.8
# pyenv global bluesky-2.7.8
# pip install ipython

sudo apt-get install libxml2-dev libxslt1-dev
sudo pip install --no-binary gdal --trusted-host pypi.smoke.airfire.org -i http://pypi.smoke.airfire.org/simple bluesky
