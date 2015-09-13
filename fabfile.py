# fab tasks for deplying and restarting bsp nodejs server, proxied via apache
#
# Example:
#  > BLUESKYWEB_SERVERS=username@hostname.com fab deploy
#
# Using Apache to proxy:
#  If you'd like to let apache proxy requests to the bluesky web server,
#  You can use something like the following
#  file: /etc/apache2/sites-available/
#    <VirtualHost *:80>
#            ServerAdmin webmaster@localhost
#            ServerName blueskyweb.bar.com
#            ServerAlias www.blueskyweb.bar.com
#
#            ProxyPass / http://127.0.0.1:9000/
#            ProxyPassReverse / http://127.0.0.1:9000/
#
#            ErrorLog /var/www/blueskyweb.bar.com/logs/error.log
#            LogLevel warn
#            CustomLog /var/www/blueskyweb.bar.com/logs/access.log combined
#    </VirtualHost>

import datetime
import os
import subprocess
import sys
from fabric import contrib
from fabric.api import *

from pyairfire.fabric.utils import (
    install_pyenv, install_pyenv_environment, add_pyenv_to_dot_file
)

from bluesky import __version__

# Only tell fabric to use .ssh config if it exists
# TODO: see how fabric searches for .ssh/config and do the same:
ssh_config = os.path.join(os.path.expanduser('~'), '.ssh/config')
if os.path.isfile(ssh_config):
    env.use_ssh_config = True

def error(msg):
    print('* {}'.format(msg))
    sys.exit(1)

##
## Role definitions and env vars
##

if not os.environ.get('BLUESKYWEB_SERVERS'):
    error('Specify BLUESKYWEB_SERVERS; ex. BLUESKYWEB_SERVERS=username@hostname.com,bar@baz.com')
env.roledefs.update({
    'web': os.environ.get('BLUESKYWEB_SERVERS').split(',')
})

PYTHON_VERSION = os.environ.get('PYTHON_VERSION') or "2.7.3"
VIRTUALENV_NAME = "bluesky-web-{}".format(PYTHON_VERSION)
REPO_GIT_URL = "https://github.com/pnwairfire/bluesky.git"
DEFAULT_BLUESKYWEB_USER = 'www-data'
DEFAULT_HOME_DIR = '/var/www/'
DEFAULT_DOT_FILE = '.profile'

##
## Helper methods
##

def env_var_or_prompt_for_input(env_var_name, msg, default):
    if not os.environ.get(env_var_name):
        sys.stdout.write('{} [{}]: '.format(msg, default))
        return raw_input().strip() or default
    else:
        return os.environ.get(env_var_name)

# Copied from http://stackoverflow.com/questions/377017/test-if-executable-exists-in-python
def cmd_exists(cmd):
    return subprocess.call("type " + cmd, shell=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE) == 0

def install_python_tools(blueskyweb_user, home_dir, dot_file):
    sudo('which git || apt-get install git-core')
    if not cmd_exists('pyenv'):
        print("Installing pyenv...")
        install_pyenv()
        add_pyenv_to_dot_file()
    print("Installing pyenv environment {}...".format(VIRTUALENV_NAME))
    install_pyenv_environment(PYTHON_VERSION, VIRTUALENV_NAME)
    for role in env['effective_roles']:
        add_pyenv_to_dot_file(user=blueskyweb_user, home_dir=home_dir,
            dot_file=dot_file)

def execute_in_virtualenv(cmd):
    """execute_in_virtualenv is for running setup/deploy/takedown type
    tasks within a vritualenv.
    """
    sudo("PYENV_VERSION={} {}".format(VIRTUALENV_NAME, cmd))

class prepare_code:
    """Context manager that clones repo on enter and deletes it on exit.
    """

    # def __init__(self, branch_or_tag_or_commit):
    #     self.branch_or_tag_or_commit = branch_or_tag_or_commit

    def __enter__(self):
        self.repo_path_name = self.get_code()
        return self.repo_path_name

    def __exit__(self, type, value, traceback):
        self.clean_up()

        # TODO: suppress exception (or just certain exceptions) by returning
        #  True no matter what (first outputting an error message) *or* by
        #  calling error function.  (type, value, and traceback are undefined
        #  unless there was an exception.)

    def get_code(self):
        bluesky_version = env_var_or_prompt_for_input('BLUESKY_VERSION',
            'Git tag, branch, or commit to deploy', 'HEAD')
        repo_dir_name = 'pnwairfire-bluesky-{}'.format(bluesky_version)

        with cd('/tmp/'):
            if contrib.files.exists(repo_dir_name):
                sudo('rm -rf %s*' % (repo_dir_name))
            run('git clone %s %s' % (REPO_GIT_URL, repo_dir_name))

        self.repo_path_name = '/tmp/{}'.format(repo_dir_name)
        with cd(self.repo_path_name):
            run('git checkout %s' % (bluesky_version))
            run('rm .python-version')
        return self.repo_path_name

    def clean_up(self):
        """Removes local repo *if it wasn't already existing*
        """
        sudo('rm -rf %s*' % (self.repo_path_name))

##
## Tasks
##

@task
@roles('web')
def setup():
    """Sets up server to run bluesky web

    Required:
     - BLUESKYWEB_SERVERS

    Optional:
     - BLUESKYWEB_USER (default: www-data)
     - PYTHON_VERSION (default: 2.7.3)

    Examples:
        > BLUESKYWEB_SERVERS=username@hostname fab setup
    """
    blueskyweb_user = env_var_or_prompt_for_input('BLUESKYWEB_USER',
        'User to run blueskyweb', DEFAULT_BLUESKYWEB_USER)
    home_dir = env_var_or_prompt_for_input('HOME_DIR',
        "blueskyweb user's home dir", DEFAULT_HOME_DIR)
    dot_file = env_var_or_prompt_for_input('DOT_FILE',
        "bluesky web user's dot file", DEFAULT_DOT_FILE)

    #sudo('which node || sudo apt-get install -y nodejs')
    install_python_tools(blueskyweb_user, home_dir, dot_file)

    print('installing dependencies...')
    sudo('apt-get install -y libnetcdf-dev')
    sudo('apt-get install -y proj')
    execute_in_virtualenv('pip install numpy==1.8.0')
    with cd('/tmp/'):
        run('wget http://download.osgeo.org/gdal/1.11.2/gdal-1.11.2.tar.gz')
        run('tar xvfz gdal-1.11.2.tar.gz')
        with cd('/tmp/gdal-1.11.2'):
            run('./configure --with-python --prefix=/usr')
            run('make')
            sudo('make install')
            sudo('ldconfig')
    execute_in_virtualenv('apt-get install -y python-gdal')
    sudo('apt-get install libxml2-dev libxslt1-dev')

    print('Creating remote root directory...')
    #sudo('mkdir -p /var/www/blueskyweb')
    sudo('mkdir -p /var/www/blueskyweb/logs/')
    sudo('chown -R www-data:www-data /var/www/blueskyweb')

@task
@roles('web')
def deploy():
    """Deploys bluesky code to server and starts web service

    Required:
     - BLUESKYWEB_SERVERS

    Optional:
     - BLUESKYWEB_USER (default: www-data)
     - BLUESKY_VERSION (default: HEAD)

    Examples:
        > BLUESKYWEB_SERVERS=username@hostname fab deploy
    """
    with prepare_code() as repo_path_name:
        with cd(repo_path_name):
            print("Installing bluesky package...")
            execute_in_virtualenv('pip install --trusted-host '
                'pypi.smoke.airfire.org -r requirements.txt')
            execute_in_virtualenv('python setup.py install')

        blueskyweb_user = env_var_or_prompt_for_input('BLUESKYWEB_USER',
            'User to run blueskyweb', DEFAULT_BLUESKYWEB_USER)
        print('Preparing upstart script and moving to /etc/init/ ...')
        upstart_script = '{}/init/blueskyweb.conf'.format(repo_path_name)
        contrib.files.sed(upstart_script, '__BLUESKYWEBUSER__', blueskyweb_user)
        contrib.files.sed(upstart_script, '__VIRTUALENV__', VIRTUALENV_NAME)
        sudo('mv {} /etc/init'.format(upstart_script))
        sudo('chown root:root /etc/init/blueskyweb.conf')
        sudo('chmod 644 /etc/init/blueskyweb.conf')

    execute(restart)

@task
@roles('web')
def restart():
    """Restarts bluesky web service

    Required:
     - BLUESKYWEB_SERVERS

    Examples:
        > BLUESKYWEB_SERVERS=username@hostname fab deploy
    """
    sudo('service blueskyweb restart')
