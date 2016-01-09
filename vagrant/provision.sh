#!/usr/bin/env bash

sudo apt-get update
#sudo apt-get upgrade

sudo apt-get install -y g++ gcc make python python-dev python-pip libnetcdf-dev proj nco
#sudo apt-get install -y proj-bin  # for ubuntu 14.04
sudo apt-get install -y tmux emacs
sudo pip install --upgrade pip

sudo pip install numpy==1.8.0
sudo apt-get install -y libgdal1-1.7.0
sudo apt-get install -y python-gdal libxml2-dev libxslt1-dev

# need to upgrade distribute and install png and freetype libs for matplotlib
sudo pip install --upgrade distribute
sudo apt-get install -y libpng12-dev libfreetype6-dev

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

sudo pip install --no-binary gdal --trusted-host pypi.smoke.airfire.org -i http://pypi.smoke.airfire.org/simple bluesky
