#!/usr/bin/python

# -*- coding: utf-8 -*-
# vim: set expandtab tabstop=4 shiftwidth=4 :

"""
IFace class and subclasses for byzantium_configd.py

ChangeLog
- 2013/09/26 - haxwithaxe - seperated interface classes from the main code.
"""
__authors__ = ['haxwithaxe me@haxwithaxe.net']
__license__ = 'GPLv3'

# Imports
import os
import os.path
import random
import re
import sys
import byzantium

# Initialize the randomizer.
random.seed()

logger = byzantium.utils.Utils().get_logger('iface')

class Utils(object):
    """Utilities for the IFace classes"""
    # map of IEEE802.11 channels to frequencies in GHz
    freq_chan_dict = {
            "2.4GHz":{1: 2.412, 2: 2.417, 3: 2.422, 4: 2.427, 5: 2.432, 6: 2.437, 7: 2.442, 8: 2.447, 9: 2.452, 10: 2.457, 11: 2.462, 12: 2.467, 13: 2.472, 14: 2.484},
            "3.6GHz":{131: 3.6575, 132: 3.66, 133: 3.665, 134: 3.67, 135: 3.6775, 136: 3.68, 137: 3.685, 138: 3.69}
            "5GHz":{128: 5.64, 64: 5.32, 132: 5.66, 7: 5.035, 8: 5.04, 9: 5.045, 11: 5.055, 12: 5.06, 16: 5.08, 149: 5.745, 153: 5.765, 157: 5.785, 161: 5.805, 34: 5.17, 36: 5.18, 165: 5.825, 38: 5.19, 40: 5.2, 42: 5.21, 44: 5.22, 46: 5.23, 48: 5.24, 136: 5.68, 52: 5.26, 183: 4.915, 56: 5.28, 185: 4.925, 187: 4.935, 60: 5.3, 189: 4.945, 192: 4.96, 196: 4.98, 140: 5.7, 184: 4.92, 100: 5.5, 104: 5.52, 188: 4.94, 108: 5.54, 112: 5.56, 116: 5.58, 120: 5.6, 124: 5.62}
            }

    def convert_frequency_to_channel(self, frequency, spectrum=defaults.get("mesh", "spectrum")):
        """ Convert frequencies (channel center) into corresponding IEEE802.11 channels
        @param  frequency       String, center of channel frequency (in GHz) of a channel in the IEEE802.11 band specified by `spectrum`
        @param  spectrum        String, of value "2.4GHz", "3.6GHz", or "5GHz" specifying the IEEE802.11 band `frequency is in`
        @return                 String, of the channel number or None if not found.
        """
        for chan, freq in freq_chan_dict[spectrum].itmes():
            if frequency == str(freq): return str(chan)
        return None

    def convert_channel_to_frequency(self, channel, spectrum=defaults.get("mesh", "spectrum")):
        """ Convert frequencies (channel center) into corresponding IEEE802.11 channels
        @param  channel         String, of channel number in the IEEE802.11 band specified by `spectrum`
        @param  spectrum        String, of value "2.4GHz", "3.6GHz", or "5GHz" specifying the IEEE802.11 band `frequency is in`
        @return                 String, of the frequency in GHz or None if not found.
        """
        channel = int(channel, 10)
        if channel in freq_chan_dict[spectrum]: return str(freq_chan_dict[spectrum][channel])
        return None

class IFace:
    """Network Interface Class
    The config section for the interface must be set either in the subclass or passed as an argument to the constructor.
    """
    def __init__(self, device, defaults=None):
        if defaults: self.defaults = defaults
        # IEEE802.11 channel number (String)
        self.channel = self.defaults.get('channel')
        # BSSID (String)
        self.bssid = self.defaults.get('bssid')
        # ESSID (String)
        self.essid = self.defaults.get('essid')
        # IPv6 Address (String) Not currently used
        self.ipv6 = self.defaults.get('ipv6_address')
        # IPv4 Address (String)
        self.ipv4 = self.defaults.get('ipv4_address')
        # IPv4 Netmask (String)
        self.netmask = self.defaults.get('ipv4_netmask')
        # Network Interface name (String, ie "eth0")
        self.device = device
        # delay between iwconfig commands when setting up the mesh interface
        self.cmd_delay = self.defaults.get("inter-command-delay", set_type=int, default=5) #FIXME reference the global value
        # used to make a distinction between mesh and client interfaces for a few things
        self.am_client = (self.defaults.get("interface-type") != "client")
        # the name to give the logger in messages we create
        self.logger_ID = "Mesh"

    def frequency(self):
        """ Return the frequency that corresponds to our channel
        @return         String, frequency in GHz
        """
        return convert_channel_to_frequency(self.channel)

    def set_down(self):
        """ Turn off the interface. 
        Runs ifconfig <interface> down
        @return         Return value of iwconfig
        """
        return ifconfig(self.device, 'down', delay=cmd_delay)

    def set_up(self):
        """ Turn on the interface.
        Runs ifconfig <interface> up
        @return         Return value of iwconfig
        """
        return ifconfig(self.device, 'up', delay=cmd_delay)

    def set_mode(self, new_mode=None):
        """ Set the mode of operation for the wireless device.
        @param  new_mode    String, mode to set the device to if the one in self.mode is not wanted.
        @return         Return value of iwconfig
        """
        return iwconfig(self.device, 'mode', new_mode or self.mode, delay=cmd_delay)

    def set_essid(self, new_essid=None):
        """ Set the ESSID of the AP to connect to or the ESSID to announce while running in AdHoc mode.
        @return         Return value of iwconfig
        """
        return iwconfig(self.device, 'essid', new_essid or self.essid, delay=cmd_delay)

    def set_bssid(self, new_bssid=None):
        """ Set the BSSID of the AdHoc network to connect to.
        @return         Return value of iwconfig
        """
        return iwconfig(self.device, 'ap', self.bssid, delay=cmd_delay)

    def set_channel(self, new_channel=None):
        """ Set the IEEE802.11 channel of the wireless interface.
        @return         Return value of iwconfig
        """
        return iwconfig(self.device, 'channel', channel or self.channel, delay=cmd_delay)

    def validate(self):
        """ Check if the values returned by iwconfig match what we want set.
        @return     Boolean, True if values are correct, False if they are not.
        """
        # Ask iwconfig what it sees
        output = iwconfig(self.device, pipe=True)
        # parse the output from iwconfig into chunks we can recognize
        mode, essid, bssid, freq = self._parse_iwconfig(output.readlines())
        # Is our mode correct?
        if not self.correct_mode(mode):
            logger.debug("Wrong mode (%s) on interface %s", mode, self.device)
            return False
        # Is our ESSID correct? 
        elif not self.correct_essid(essid):
            logger.debug("Wrong ESSID (%s) on interface %s", essid, self.device)
            return False
        # Is our BSSID Correct
        elif not self.correct_bssid(bssid):
            logger.debug("Wrong BSSID (%s) on interface %s", bssid, self.device)
            return False
        # Is our frequency/channel correct?
        elif not self.correct_frequency(freq):
            logger.debug("Wrong frequency (%s) on interface %s", freq, self.device)
            return False
        # Since nothing was wrong we return True
        return True

    def _parse_iwconfig(self, output):
        """ Parse the output of iwconfig into the values we require for checking.
        @param  output  List of lines of output from iwconfig
        @return         Tuple (mode, essid, bssid, freq)
        """
        # set everything to None so it exists on the other end and is clearly unset if it isn't found
        mode, essid, bssid, freq = None
        # go line by line and pull out values
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
        """ Correct mode?
        @param  real_mode   String, the mode found by iwconfig.
        @return             Boolean, True if they match False if not
        """
        if real_mode == self.mode: return True
        return False

    def correct_essid(self, real_essid):
        """ Correct ESSID?
        @param  real_mode   String, the ESSID found by iwconfig.
        @return             Boolean, True if they match False if not
        """
        if real_essid == self.essid: return True
        return False

    def correct_bssid(self, real_bssid):
        """ Correct BSSID?
        @param  real_mode   String, the BSSID found by iwconfig.
        @return             Boolean, True if they match False if not
        """
        if real_bssid == self.bssid: return True
        return False

    def correct_frequency(self, real_freq):
        """ Correct frequency?
        @param  real_mode   String, the frequency (in GHz) found by iwconfig.
        @return             Boolean, True if they match False if not
        """
        # Correct *frequency* (because iwconfig doesn't report channels)?
        if real_freq == self.frequency(): return True
        return False

    def random_ip_v4(self, network, netmask):
        """ Generate a pseudorandom IP address
        @param  network     String, network description (ie 192.168.0.0)
        @param  netmask     (not used but should be) String, netmask for the whole space available to guess in (ie. 255.255.0.0 for 192.168.0.0-192.168.255.0) specified as 'gen_netmask' in settings
        @return             A psuedorandom IPv4 address as a list of strings.
        """
        #   For every octet in `network` that is '0' and comes after all non-'0'
        # octets pick a random replacement counting in reverse so we don't hit
        # a '0' that occurs before a non-'0'
        for octet in range(0, len(network)).reverse():
            if network[octet] != '0': break
            network[octet] = str(random.randint(0, 254))
        return network

    def _arping(self, addr):
        """ Wrapper over the wrapper of arping
        @param          String, ip address to arping
        @return         Return value of arping
        """
        return arping( '-c', '5', '-D', '-f', '-q', '-I', self.device, addr)

    def get_ip_v4_addr(self, network=None, netmask=None):
        """ Get an IPv4 address for this interface
        @param  network     String, the network description (ie. 192.168.0.0)
        @param  netmask     String, the netmask for generating the new IP
        @return             String, the new IPv4 address
        """
        if not network: network = self.defaults.get("ipv4_network")
        if not netmask: netmask = self.defaults.get("gen_netmask")
        # make the IP-like strings into arrays
        network = network.split('.')
        netmask = netmask.split('.')
        # get a pseudorandom IP
        addr = self.random_ip_v4([network], [netmask])
        # if this is a client interface set the last octet to '1'
        if self.am_client: addr[-1] = "1"
        addr = '.'.join(addr)
        # try to find an unused IP
        while not self._arping(addr):
            addr = self.random_ip_v4([network], [netmask])
        # use the last one tried even if it was in use.
        self.ipv4 = addr
        return self.ipv4

    def load(self, ipv4_network=None, gen_netmask=None):
        """ Get the interface up and running
        @param  network
        @param  netmask
        """
        self.get_ip_v4_addr(network=ipv4_network, netmask=gen_netmask)
        self.set_ip()
        self.set_up()
        logger.info("%s interface %s configured." % (self.logger_ID, self.device))

class MeshIface(IFace):
    """ Mesh network interface"""
    logger_ID = "Mesh"
    def __init__(self, device, defaults):
        """Set the device name on initialization
        @param  device      String, network device name (ie. 'eth0')
        @param  defaults    byzantium.config.Config object with the section describing tis interface.
        """
        self.device = device
        self.defaults = defaults.get_section(config_section)

    def configure(self, max_tries=defaults.get("configd", "max-tries", set_type=int, default=15)):
        """ Attempt to configure the mesh interface with iwconfig
        @param  max_tries       Int, Maximum number of times to attempt to configure the interface.
        @return                 Boolean, True if successful, False if not
        """
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
        # return whether we failed hard or succeeded
        return self.validate()

class ClientIFace(IFace):
    """ Client network interface """
    config_section = "client"
    logger_ID = "Client"
    am_client = True
    def __init__(self, device, sub_device_number=None):
        """Set the device name on initialization
        @param  device              String, network device name (ie. 'eth0')
        @param  sub_device_number   Int or String of the digit to append as the subdevice number
        """
        if sub_device_number != None:
            self.device = "%s:%s" % (device, str(sub_device_number))
        else:
            # if we don't get a subdevice number we will pretend we don't need one
            self.device = device

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

