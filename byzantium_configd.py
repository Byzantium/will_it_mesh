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

# Initialize the randomizer.
random.seed()

defaults = byzantium.conf('will_it_mesh.conf')
logger = defaults.utils.get_logger('will_it_mesh')

freq_chan_dict = {
        "2.4GHz":{1: 2.412, 2: 2.417, 3: 2.422, 4: 2.427, 5: 2.432, 6: 2.437, 7: 2.442, 8: 2.447, 9: 2.452, 10: 2.457, 11: 2.462, 12: 2.467, 13: 2.472, 14: 2.484},
        "3.6GHz":{131: 3.6575, 132: 3.66, 133: 3.665, 134: 3.67, 135: 3.6775, 136: 3.68, 137: 3.685, 138: 3.69}
        "5GHz":{128: 5.64, 64: 5.32, 132: 5.66, 7: 5.035, 8: 5.04, 9: 5.045, 11: 5.055, 12: 5.06, 16: 5.08, 149: 5.745, 153: 5.765, 157: 5.785, 161: 5.805, 34: 5.17, 36: 5.18, 165: 5.825, 38: 5.19, 40: 5.2, 42: 5.21, 44: 5.22, 46: 5.23, 48: 5.24, 136: 5.68, 52: 5.26, 183: 4.915, 56: 5.28, 185: 4.925, 187: 4.935, 60: 5.3, 189: 4.945, 192: 4.96, 196: 4.98, 140: 5.7, 184: 4.92, 100: 5.5, 104: 5.52, 188: 4.94, 108: 5.54, 112: 5.56, 116: 5.58, 120: 5.6, 124: 5.62}
        }

def shell(*cmd, **kwargs):
    if 'pipe' in kwargs and kwargs['pipe']:
        retval = subprocess.Popen(cmd, stdout=subprocess.PIPE).stdout
    retval = subprocess.Popen(cmd)
    if 'delay' in kwargs and delay > 0:
        time.sleep(delay)
    return retval

def ifconfig(*args, **kwargs):
    cmd = ['/sbin/ifconfig']+args
    return shell(*cmd, **kwargs)

def iwconfig(*args, **kwargs):
    cmd = ['/sbin/iwconfig']+args
    return shell(*cmd, **kwargs)

def route(*args, **kwargs):
    cmd = ['/sbin/route']+args
    return shell(*cmd, **kwargs)

def arping(*args, **kwargs):
    cmd = ['/sbin/arping']+args
    shell(*cmd, **kwargs)

def convert_frequency_to_channel(frequency, spectrum=defaults.get("mesh", "spectrum")):
    for chan, freq in freq_chan_dict[spectrum].itmes():
        if frequency == str(freq): return chan
    return None

def convert_channel_to_frequency(channel, spectrum=defaults.get("mesh", "spectrum")):
    if channel in freq_chan_dict[spectrum]: return freq_chan_dict[spectrum][channel]
    return None

class IFace:
    channel = defaults.get('mesh', 'channel')
    bssid = defaults.get('mesh', 'bssid')
    essid = defaults.get('mesh', 'essid')
    ipv6 = None
    ipv4 = None
    netmask = defaults.get('mesh', 'ipv4_netmask')
    device = None
    cmd_delay = defaults.get("configd", "inter-command-delay", set_type=int, default=5)
    am_client = False
    config_section = "mesh"
    logger_ID = "Mesh"

    def frequency(self):
        return convert_channel_to_frequency(self.channel)

    def set_down(self):
        """ Turn off the interface. """
        return ifconfig(self.device, 'down', delay=cmd_delay)

    def set_up(self):
        """ Turn on the interface. """
        return ifconfig(self.device, 'up', delay=cmd_delay)

    def set_mode(self, new_mode=None):
        return iwconfig(self.device, 'mode', new_mode or self.mode, delay=cmd_delay)

    def set_essid(self, new_essid=None):
        return iwconfig(self.device, 'essid', new_essid or self.essid, delay=cmd_delay)

    def set_bssid(self, new_bssid=None):
        return iwconfig(self.device, 'ap', wireless.bssid, delay=cmd_delay)

    def set_channel(self, new_channel=None):
        return iwconfig(self.device, 'channel', channel or self.channel, delay=cmd_delay)

    def validate(self):
        output = iwconfig(self.device, pipe=True)
        mode, essid, bssid, freq = self._parse_iwconfig(output.readlines())
        if not self.correct_mode(mode):
            logger.debug("Wrong mode (%s) on interface %s", mode, self.device)
            return False
        elif not self.correct_essid(essid):
            logger.debug("Wrong ESSID (%s) on interface %s", essid, self.device)
            return False
        elif not self.correct_bssid(bssid):
            logger.debug("Wrong BSSID (%s) on interface %s", bssid, self.device)
            return False
        elif not self.correct_frequency(freq):
            logger.debug("Wrong frequency (%s) on interface %s", freq, self.device)
            return False
        return True

    def _parse_iwconfig(self, output):
        mode, essid, bssid, freq = None
        for line in output:
            if re.search("Mode", line):
                mode = line.split(' ')[0].split(':')[1]
            elif re.search("ESSID", line):
                essid = line.split(' ')[-1].split(':')[1]
            elif re.search("Cell", line):
                bssid = line.split(' ')[-1]
            elif re.search("Frequency", line):
                freq = line.split(' ')[2].split(':')[1]
        return mode, essid, bssid, freq

    def correct_mode(self, real_mode):
        """ Correct mode? """
        if real_mode == self.mode: return True
        return False

    def correct_essid(self, real_essid):
        """ Correct ESSID? """
        if real_essid == self.essid: return True
        return False

    def correct_bssid(self, real_bssid):
        """ Correct BSSID? """
        if real_bssid == self.bssid: return True
        return False

    def correct_frequency(self, real_freq):
        """ Correct frequency? """
        # Correct *frequency* (because iwconfig doesn't report channels)?
        if real_freq == self.frequency(): return True
        return False

    def random_ip_v4(self, network, netmask):
        """ Generate a pseudorandom IP address """
        for octet in range(0, len(network)).reverse():
            if network[octet] == '0':
                network[octet] = str(random.randint(0, 254))
        return network

    def _arping(self, addr):
        return arping( '-c', '5', '-D', '-f', '-q', '-I', self.device, addr)

    def get_ip_v4_addr(self, network=defaults.get("mesh", "gen_netmask"), netmask=defaults.get("mesh", "gen_netmask")):
        network = network.split('.')
        netmask = netmask.split('.')
        addr = self.random_ip_v4([network], [netmask])
        if self.am_client: addr[-1] = "1"
        addr = '.'.join(addr)
        while not self._arping(addr):
            addr = self.random_ip_v4([network], [netmask])
        self.ipv4 = addr
        return self.ipv4

    def load(self):
        self.get_ip_v4_addr(defaults.get(self.config_section, 'ipv4_network'), defaults.get(self.config_section, 'gen_netmask')
        self.set_ip()
        self.set_up()
        logger.info("%s interface %s configured." % (self.logger_ID, self.device))

class MeshIface(IFace):
    config_section = "mesh"
    logger_ID = "Mesh"

    def __init__(self, device):
        self.device = device

    def configure(self, max_tries=defaults.get("configd", "max-tries", set_type=int, default=15)):
        logger.info("Attempting to configure interface %s." % wireless)
        # Turn off the interface.
        self.set_down()
        # Set wireless parameters on the interface.  Do this by going into a loop
        # that tests the configuration for correctness and starts the procedure
        # over if it didn't take the first time.
        # We wait a few seconds between iwconfig operations because some wireless
        # chipsets are pokey (coughAtheroscough) and silently reset themselves if
        # you try to configure them too rapidly, meaning that they drop out of
        # ad-hoc mode.
        remaining_attempts = max_tries
        while not self.validate() or remaining_attemts > 0:
            # Configure the wireless chipset.
            self.set_mode()
            self.set_bssid()
            self.set_channel()
            remaining_attempts -= 1
        # Turn the interface back on.
        self.set_up()
        return self.validate()

class ClientIFace(IFace):
    config_section = "client"
    logger_ID = "Client"
    def __init__(self, device, sub_device_number=None):
        self.am_client = True
        if sub_device_number != None:
            self.device = "%s:%s" % (device, str(sub_device_number))
        else:
            self.device = device

def start_captive_portal(mesh, client):
    script_path = defaults.get('captive-portal', 'script', default='captive_portal.py')
    return shell(script_path, '-i', client.device, '-a', client.ipv4)

def get_network_devices(exclude=[]):
    """ Enumerate all network interfaces. 
    """
    interfaces = os.listdir('/sys/class/net')
    # Remove the loopback interface and any other specified interfaces
    for x in exclude+['lo']:
        if x in interfaces:
            interfaces.remove(x)
    if not interfaces:
        raise byzantium.exception.DeviceException("ERROR: No interfaces found.")

def get_wireless_devices(exclude=[]):
    """ Enumerate all the wireless interfaces.
    """
    get_network_devices(exclude)
    # For each network interface's pseudofile in /sys, test to see if a
    # subdirectory 'wireless/' exists.  Use this to sort the list of
    # interfaces into wired and wireless.
    wireless = []
    for i in interfaces:
        if os.path.isdir("/sys/class/net/%s/wireless" % i):
            wireless.append(i)
    if not wireless:
        raise byzantium.exception.DeviceException("ERROR: No wireless interfaces found.")
    return wireless

def make_hosts_file(mesh, client):
    """ Generate and write /etc/hosts.mesh from the values given by `client` and `mesh`
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
    """ Generate an /etc/dnsmasq.conf.include file. """
    prefix = '.'.join(client.ipv4.split('.')[:3])
    ipv4_template = "%s.%d"
    start = ipv4_template % (prefix, 2)
    end = ipv4_template % (prefix, 254)
    dhcp_range = "dhcp-range=%s,%s,5m" % (start, end)
    include_file = open(defaults.get("files", "dnsmasq-include"), 'w')
    include_file.write(dhcp_range)
    include_file.close()

def init_dnsmasq(action="restart"):
    """ poke at dnsmasq. """
    logger.info("%s dnsmasq." % action.upper())
    return shell('/etc/rc.d/rc.dnsmasq', action.lower())

def start_olsrd(mesh):
    """ poke at olsrd. """
    logger.info("Starting routing daemon.")
    return shell('/usr/sbin/olsrd', '-i', mesh.device)

def add_commotion_route(mesh, client):
    # Add a route for any Commotion nodes nearby.
    logger.info("Adding Commotion route...")
    route('add', '-net', defaults.get("commotion", "ipv4_network"), 'netmask', defaults.get("commotion", "ipv4_netmask"), 'dev', mesh.device)


    # Start the captive portal daemon on that interface.
    start_captive_portal(mesh, client)
    logger.info("Started captive portal daemon.")

    make_hosts_file(mesh, client)
    make_dnsmasq_include(mesh, client)
    init_dnsmasq(action="restart")
    start_olsrd(mesh)

def main(args):
    excludes = []
    # eventually grab values from the commandline args here
    wireless = get_wireless_devices(exclude=excludes)
    if not wireless: return None
    congiured_mesh = False
    for iface in wireless:
        mesh = MeshIFace(iface)
        if mesh.configure():
            congiured_mesh = True
            break
    if not configured_mesh: return None
    mesh.load()
    # Setup client interface.
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

