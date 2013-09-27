#!/usr/bin/python

# -*- coding: utf-8 -*-
# vim: set expandtab tabstop=4 shiftwidth=4 :

# byzantium_configd.py - A (relatively) simple daemon that automatically
# configures wireless interfaces on a Byzantium node.  No user interaction is
# required.  Much of this code was taken from the control panel, it's just
# been assembled into a more compact form.  The default network settings are
# the same ones used by Commotion Wireless, so this means that our respective
# projects are now seamlessly interoperable.  For the record, we tested this
# in Red Hook in November of 2012 and it works.

# This utility is less of a hack, but it's far from perfect.

""" ChangeLog
- 2013/09/26 - haxwithaxe - rewrote/reorganized into functions and classes and hooked into the byzantium python libs
- The Doctor [412/724/301/703] [ZS|Media] <drwho at virtadpt dot net>
    This utility is less of a hack, but it's far from perfect.
"""
__authors__ = ['The Doctor [412/724/301/703] [ZS|Media] <drwho at virtadpt dot net>', 'haxwithaxe me@haxwithaxe.net']
__license__ = 'GPLv3'

# Imports
import os
import os.path
import random
import re
import subprocess
import sys
import time
import byzantium


defaults = byzantium.conf('will_it_mesh.conf')
logger = defaults.utils.get_logger('will_it_mesh')

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

def start_captive_portal(mesh, client):
    """ Start the captive portal
    @param  mesh        MeshIface instance
    @param  client      ClientIFace instance
    @return             Return value of captive_portal.py
    """
    script_path = defaults.get('captive-portal', 'script', default='captive_portal.py')
    return shell(script_path, '-i', client.device, '-a', client.ipv4)

def get_network_devices(exclude=[]):
    """ Enumerate all network interfaces.
    @param  exclude     List of network deices to exclude. ('lo' is always excluded)
    @return             List of network devices present.
    """
    # get a list of all of the network devices available now.
    interfaces = os.listdir('/sys/class/net')
    # Remove the loopback interface and any other specified interfaces
    for x in exclude+['lo']:
        if x in interfaces:
            interfaces.remove(x)
    # if we don't find anything pitch a fit
    if not interfaces:
        raise byzantium.exception.DeviceException("ERROR: No interfaces found.")
    return interfaces

def get_wireless_devices(exclude=[]):
    """ Enumerate all the wireless interfaces.
    @param  exclude     List of network deices to exclude. ('lo' is always excluded)
    @return             List of wireless network devices present.
    """
    net_devices = get_network_devices(exclude=exclude)
    # For each network interface's pseudofile in /sys, test to see if a
    # subdirectory 'wireless/' exists.  Use this to sort the list of
    # interfaces into wired and wireless.
    wireless = []
    for i in net_devices:
        if os.path.isdir("/sys/class/net/%s/wireless" % i):
            wireless.append(i)
    # if we don't find any wireless devices pitch a fit
    if not wireless:
        raise byzantium.exception.DeviceException("ERROR: No wireless interfaces found.")
    return wireless

def make_hosts_file(mesh, client):
    """ Generate and write /etc/hosts.mesh from the values given by `client` and `mesh`
    @param  mesh        MeshIface instance
    @param  client      ClientIFace instance
    """
    # Build a string which can be used as a template for an /etc/hosts style file.
    prefix = '.'.join(client.ipv4.split('.')[:3])
    # Make an /etc/hosts.mesh file, which will be used by dnsmasq to resolve its
    # mesh clients.
    hosts_string = ["%s\tbyzantium.byzantium.mesh" % client.ipv4]
    for i in range(1, 255):
        client_ip = "%s.%d" % (prefix, i)
        if client_ip != client.ipv4:
            hosts_string.append("%s\tclient-%s.byzantium.mesh" % (client_ip, client_ip))
    hosts = open(defaults.get("files", "hosts.mesh"), "w")
    hosts.write('\n'.join(hosts_string))
    hosts.close()

def make_dnsmasq_include(mesh, client):
    """ Generate an /etc/dnsmasq.conf.include file.
    @param  mesh        MeshIface instance
    @param  client      ClientIFace instance
    """
    prefix = '.'.join(client.ipv4.split('.')[:3])
    ipv4_template = "%s.%d"
    start = ipv4_template % (prefix, 2)
    end = ipv4_template % (prefix, 254)
    dhcp_range = "dhcp-range=%s,%s,5m" % (start, end)
    include_file = open(defaults.get("files", "dnsmasq-include"), 'w')
    include_file.write(dhcp_range)
    include_file.close()

def init_dnsmasq(action="restart"):
    """ Poke at dnsmasq. 
    @param  action      String, parameter to pass to /etc/rc.d/rc.dnsmasq. It must be valid as per that script's requirements.
    @return             Return value of '/etc/rc.d/rc.dnsmasq'
    """
    logger.info("%s dnsmasq." % action.upper())
    return shell('/etc/rc.d/rc.dnsmasq', action.lower())

def start_olsrd(mesh):
    """ Start olsrd.
    @param  mesh        MeshIface instance
    @return             Return value of '/usr/sbin/olsrd'
    """
    logger.info("Starting routing daemon.")
    return shell('/usr/sbin/olsrd', '-i', mesh.device)

def add_commotion_route(mesh, client):
    """ Add the Commotion-Wireless route to the route table so we can jump in on their networks.
    @param  mesh        MeshIface instance
    @param  client      ClientIFace instance
    @return             Return value of 'route'
    """
    # Add a route for any Commotion nodes nearby.
    logger.info("Adding Commotion route...")
    return route('add', '-net', defaults.get("commotion", "ipv4_network"), 'netmask', defaults.get("commotion", "ipv4_netmask"), 'dev', mesh.device)

def main(args):
    """ Entry point of script.
    @param  args    List of arguments passed to the script
    """
    excludes = []
    # eventually grab values from the commandline args here
    # this throws exceptions if it doesn't find anything
    wireless = get_wireless_devices(exclude=excludes)
    # set our little state token
    congiured_mesh = False
    # walk through all the interfaces until we find a working one or run out
    for iface in wireless:
        mesh = MeshIFace(iface)
        if mesh.configure():
            congiured_mesh = True
            break
    # if nothing is configured stop here
    if not configured_mesh: return None
    # else load up the mesh interface
    mesh.load()
    # and setup the client interface.
    client = ClientIFace(mesh.device, client_number)
    client.load()
    # add the commotion-wireless route
    add_commotion_route(mesh, client)
    # Start the captive portal daemon on that interface.
    start_captive_portal(mesh, client)
    logger.info("Started captive portal daemon.")
    # Make some config files
    make_hosts_file(mesh, client)
    make_dnsmasq_include(mesh, client)
    # Poke some services we changed configs for
    init_dnsmasq(action="restart")
    start_olsrd(mesh)

# FIXME UNCOMMENT try below for production
#try:
    main(sys.argv)
#except Exception as e:
#    sys.exit(0)

