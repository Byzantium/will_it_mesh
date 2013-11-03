#!/usr/bin/python

# -*- coding: utf-8 -*-
# vim: set expandtab tabstop=4 shiftwidth=4 :

""" byzantium_configd.py - A (relatively) simple daemon that automatically
configures wireless interfaces on a Byzantium node.  No user interaction is
required.  Much of this code was taken from the control panel, it's just
been assembled into a more compact form.  The default network settings are
the same ones used by Commotion Wireless, so this means that our respective
projects are now seamlessly interoperable.  For the record, we tested this
in Red Hook in November of 2012 and it works.

ChangeLog
- 2013/09/26 - haxwithaxe - rewrote/reorganized into functions and classes and hooked into the byzantium python libs
"""
__authors__ = ['haxwithaxe me@haxwithaxe.net']
__license__ = 'GPLv3'

# Imports
import sys
from byzantium.configd import *

try:
    startup.on_startup(sys.argv)
except Exception as e:
    sys.exit(0)

