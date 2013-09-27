#!/usr/bin/python

# -*- coding: utf-8 -*-
# vim: set expandtab tabstop=4 shiftwidth=4 :

""" shell.py - a library to support byzantium_configd.py accessing the command line utilities it needs

ChangeLog
- 2013/09/26 - haxwithaxe - separated from byzantium_configd.py
"""
__authors__ = ['haxwithaxe me@haxwithaxe.net']
__license__ = 'GPLv3'

# Imports
import os
import os.path
import subprocess
import sys
import time
import byzantium

defaults = byzantium.config.Config()
logger = defaults.utils.get_logger('shell')

def shell(*cmd, **kwargs):
    """ Wrapper for subprocess with some bells and whistles.
    @param  *cmd        List of strings that are passed to subprocess.Popen
    @param  **kwargs    See following parameters.
    @param  pipe        Boolean, if True then return stdout from the subprocess.
    @param  delay       Int, denoting the time in seconds to delay after running the command.
    @return             Return code or String if `pipe` is True.
    """
    if 'pipe' in kwargs and kwargs['pipe']:
        retval = subprocess.Popen(cmd, stdout=subprocess.PIPE).stdout
    retval = subprocess.Popen(cmd)
    if 'delay' in kwargs and delay > 0:
        time.sleep(delay)
    return retval

def ifconfig(*args, **kwargs):
    """Wrapper for ifconfig
    @param  *cmd        argumants to pass to ifconfig
    @param  **kwargs    See `shell` docs for **kwargs
    @return             See `shell` docs for @return
    """
    cmd = ['/sbin/ifconfig']+args
    return shell(*cmd, **kwargs)

def iwconfig(*args, **kwargs):
    """Wrapper for iwconfig
    @param  *cmd        argumants to pass to iwconfig
    @param  **kwargs    See `shell` docs for **kwargs
    @return             See `shell` docs for @return
    """ 
    cmd = ['/sbin/iwconfig']+args
    return shell(*cmd, **kwargs)

def route(*args, **kwargs):
    """Wrapper for route
    @param  *cmd        argumants to pass to route
    @param  **kwargs    See `shell` docs for **kwargs
    @return             See `shell` docs for @return
    """ 
    cmd = ['/sbin/route']+args
    return shell(*cmd, **kwargs)

def arping(*args, **kwargs):
    cmd = ['/sbin/arping']+args
    shell(*cmd, **kwargs)

