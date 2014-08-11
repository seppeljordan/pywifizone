# PyWifiZone - Tries to extract geodata from wifi presence
# Copyright (C) 2014 baldulin
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
from subprocess import call, Popen, PIPE
from collections import defaultdict
from itertools import izip_longest as izip

import sys
import re
import curses
import time
import signal
import pickle

# Console Variables
recr = 0
slp = 5

# Device Variable
device = None

# Data For Current Fetch
data = {}

# Regex Variables
re_cell_start = re.compile(r"^\s*Cell ([0-9]+) - Address: ([A-F0-9:]+)$")
re_field = re.compile(r"^\s*([a-zA-Z ]+):\s*\"?\s*([^\"]*)\s*\"?\s*$")
re_qual = re.compile(r"^\s*Quality=(\d+)/(\d+)\s+Signal level=-(\d+) dBm$")

def cmd():
    """ Returns the command for iwlist output """
    global device
    if device is not None:
        return ["iwlist", device, "scan"]
    return ["iwlist", "scan"]


class Zone(object):
    """ Zone Class descripes the behavouir of multiple networks """

    def __init__(self):
        """ Creates Data Dict """
        self.data = dict()
    
    def update(self, cells):
        """ Updates with new data """
        for essid in cells.iterkeys():
            zw = self.data[essid] if essid in self.data else ZoneWifi()
            zw.update(cells[essid].signal)
            self.data[essid] = zw

        for essid in list(set(self.data.iterkeys()) - set(cells.iterkeys())):
            zw = self.data[essid]
            zw.updateUnavail()

    def compare(self, other):
        """ Compares with another Zone """
        a = set(self.data.iterkeys())
        b = set(other.data.iterkeys())

        missing = list(a-b)
        overflow = list(b-a)
        
        compares = dict()
        c = 0
        n = 0
        for essid in list(a & b):
            za = self.data[essid]
            zb = other.data[essid]

            compares[essid] = za.compare(zb)
            n += 1
            c += compares[essid]
        
        c = c / n
        
        return (missing, overflow, compares, c)


class ZoneWifi(object):
    """ Describes a Wifi in a Zone """

    def __init__(self):
        """ Initializes the Wifi zone values 
            
            @var smax    Maximal Signal Strength
            @var smin    Minimal Signal Strength
            @var smean     Mean value
            @var svar     Varianz
            @var unavail How Long network can't be reached
        """
        self.smax = -1
        self.smin = -1
        self.smean = -1
        self.var = 0
        self.unavail = 0
    
    def __repr__(self):
        """ Returns Basic Info in a String """
        return "Max:%d;Min:%d;Mean:%f;Var:%f" % \
                (self.smax, self.smin, self.smean, self.var)

    # Same for string
    __str__ = __repr__
    
    def updateUnavail(self):
        try:
            self.unavail = (self.unavail+1)/2.
        except:
            self.unavail = 0

    def update(self, cur):
            """ Update with new signal strength """
            if self.smax == -1 or self.smax < cur:
                self.smax = cur
            if self.smin == -1 or self.smin > cur:
                self.smin = cur

            # Recalculate Mean value
            if self.smean == -1:
                self.smean = cur
            else:
                # Calculate Varianz first
                self.var = (self.var + abs(cur - self.smean))/2
                # Now Mean value
                self.smean = (self.smean + cur)/2

            # Update Unavail counter
            try:
                self.unavail = self.unavail / 2.
            except:
                self.unavail = 0

    
    def compare(self, other):
        """ Compares with another ZoneWifi object """
        # The more percent of the min max range you got the better:
        return (self._intvalperc(self.smax, self.smin, other.smax, other.smin) \
            + self._intvalperc(other.smax, other.smin, self.smax, self.smin))/4\
            + self._meanperc(self.smean, other.smean)/2
    
    def _meanperc(self, amean, bmean):
        """ Calculates the difference by mean value """
        return 1-abs(amean - bmean)/90.

    def _intvalperc(self,amax, amin, bmax, bmin):
        """ Calculates the difference by min,max overlap """
        # Size of interval
        l = amax - amin
        # Some conditions where its bound to be zero
        if amax < bmin:
            c = 0
        elif amin > bmax:
            c = 0
        else:
            # Now theres an intersection
            if amax > bmax:
                nmax = bmax
            else:
                nmax = amax

            if amin < bmin:
                nmin = bmin
            else:
                nmin = amin

            try:
                c = (nmax - nmin)/(float(l))
            except:
                if bmax == amax and bmin == amin:
                    c = 1
                else:
                    c = 0
        return c




class Cell(object):
    """ Basic Data Object directly filled from iwlist output """

    def __init__(self):
        """ Initializes everything empty """
        self.extra = ""
        self.encryptionkey = ""
        self.bitrates = ""
        self.signal = ""
        self.frequency = ""
        self.essid = ""
        self.address = ""
        self.groupchiper = ""
        self.ie = ""
        self.quality = ""
        self.channel = ""
        self.mode = ""

    def __repr__(self):
        """ Returns Cell String """
        return "Cell(essid=%s, address=%s, quality=%s, signal=-%d)" % \
            (self.essid, self.address, self.quality, self.signal)

    # String is also repr
    __str__ = __repr__


def fetch():
    """ Fetch a new global data dict """
    global data

    # Current Cell
    cell_cur = None
    # Scanner for network cells and fields
    g = scan()
    # New Data Dict
    data = dict()
    # Create Buffer Cell
    o = Cell()

    # Iterate over cells
    for f in g:
        if isinstance(f, str):
            if cell_cur is not None:
                data[o.essid] = o
                o = Cell()

            cell_cur = int(f)
        else:
            setattr(o, f[0].lower().replace(" ","_"), f[1])
    

    
def scan():
    """ Generates Cell Data from iwlist """
    global re_cell_start, re_qual, re_field
    proc = Popen(cmd(), stdout=PIPE, stderr=PIPE)

    # Do as long as possible
    while True:
        # Read line
        line = proc.stdout.readline()

        # If Line is existing
        if line != '':
            line = line.rstrip()

            # Is it a new Cell?
            obj = re_cell_start.match(line)
            if obj is not None:
                yield obj.group(1)
                yield ("Address", obj.group(2))
                continue
            
            # Is it just a field
            obj = re_field.match(line)
            if obj is not None:
                yield obj.groups()
                continue

            # Is it the Signal Strength
            obj = re_qual.match(line)
            if obj is not None:
                yield ("Quality", "%s/%s" % (obj.group(1),obj.group(2)))
                yield ("Signal",int(obj.group(3)))
        else:
            # End of output
            break

def _current(_zone, zones):
    current = None
    since = None
    for zone in _update(_zone, slp):
        stat = dict()
        for o in zones:
            (missing, overflow, compare, c) = zones[o].compare(zone)
            stat[o] = c

        cur = sorted(stat.iterkeys(), key=lambda x: -stat[x] )[0]
        
        if current == None:
            current = cur
            since = time.time()

        if current != cur:
            print "\rMoved from \x1B[34m%s\x1B[0m (stayed" \
                + "\x1B[32m%.2f\x1B[0m min) to \x1B[34m%s\x1B[0m" % \
                (current, (time.time()-since)/60., cur)

            current = cur
            since = time.time()

        sys.stdout.write("\rCurrent: \x1B[34m%s\x1B[0m Since:"\
                + "\x1B[32m%.2f\x1B[0m min\t\t\t" % \
                (current, (time.time()-since)/60.))
        

            
            

def _update(zone, slp=5):
    """ Updates the global data dict """
    global data, recr

    for i in _countreset(recr):
        if i:
            zone = Zone()

        fetch()
        zone.update(data)

        yield zone
        time.sleep(slp)

def _countreset(recr = 0):
    if recr == 0:
        while True:
            yield False
    else:
        while True:
            for i in range(recr):
                yield False
            yield True
        

def _killcurses(signal, frame):
    """ Kills Application if curses was used """
    curses.echo()
    curses.nocbreak()
    curses.endwin()
    # End Session
    sys.exit(0)

def _kill(signal, frame):
    """ Kills Application without curses """
    # End Session
    print ""
    sys.exit(0)

def _interactive(_zone, zones):
    """ Starts Interactive Compare Info """
    # Initialize curses
    stdscr = curses.initscr()
    curses.start_color()
    curses.noecho()
    curses.cbreak()
    stdscr.refresh()

    # Register Handler
    signal.signal(signal.SIGINT, _killcurses)

    # Initialize Colors
    curses.init_pair(1, curses.COLOR_RED, 0)
    curses.init_pair(2, curses.COLOR_GREEN,0 )
    curses.init_pair(3, curses.COLOR_YELLOW,0 )
    curses.init_pair(4, curses.COLOR_BLUE, 0)
    curses.init_pair(5, curses.COLOR_MAGENTA, 0)
    curses.init_pair(6, curses.COLOR_CYAN, 0)

    # Update Zones
    for zone in _update(_zone, slp):
        stat = list()
        
        # Compare Zones
        for o in zones:
            (missing, overflow, compare, c) = zones[o].compare(zone)
            stat.append([o, c, len(missing), len(overflow)])

        # Get Colored default dict
        d = defaultdict(lambda:1)
        d[0] = 2;d[1] = 6;d[2] = 3;d[3] = 3
        g = (d[i] for i in range(len(stat)))

        # Print Title
        stdscr.addstr(0,0,"Compare:")

        # Add Color attribute
        for i,t in zip(g,sorted(range(len(stat)), key=lambda x: -stat[x][1])):
            stat[t].insert(1,i)

        # Print to Screen
        for i,t in enumerate(stat):
            stdscr.addstr(i+1, 0, t[0]+":", curses.color_pair(4))
            stdscr.addstr(i+1,11, str(t[2])[:5], curses.color_pair(t[1]))
            stdscr.addstr(i+1,16,"(%2d/%2d)    " % (t[3], t[4]))
        
        # Refresh
        stdscr.refresh()

def updateZone(zone, n, slp = 5):
    global data

    """ Update Zones to accumulate info """
    for i in range(n):
        # Fetch data:
        fetch()
        zone.update(data)
        data = dict()
        time.sleep(slp)

    return zone

def _basic(_zone, zones, short = False):
    """ Basic output (the default) or short """
    for zone in _update(_zone, slp):
        for o in zones:        
            # Compare the stuff
            (missing, overflow, compare, c) = zones[o].compare(zone)
            
            if short:
                print ("Compare: \x1B[34m%8s\x1B[0m  Score:\x1B[31m%f\x1B[0m"\
                        + "Missing:%d Overflow:%d")\
                        % (o, c, len(missing), len(overflow))
            else:
                # Print Long Basic
                print "Compare: \x1B[34m%s\x1B[0m:" % o
                print ("\tMissing: \x1B[33m%d\x1B[0m\t\t"\
                        + "Overflow: \x1B[33m%d\x1B[0m")\
                        % (len(missing), len(overflow))

                # Print The Missing and overflown wifis
                for m,n in izip(missing, overflow):
                    m = "" if m is None else m
                    n = "" if n is None else n
                    print "\t\x1B[33m%-15s\x1B[0m\t\t\x1B[33m%-15s\x1B[0m" \
                        % (m[:15],n[:15]) 
        
                # Print Comparisson
                for essid in compare:
                    print "\tEssid:%15s Score: %f" % \
                            (essid[:15], compare[essid])
                print "\x1B[32mTotal Score\x1B[0m:%f" % c

def _score(_zone, zones):
    """ Updating Score online for small number of Zones """
    for zone in _update(_zone, slp):
        stat = list()

        # Compare all stuff
        for o in zones:
            (missing, overflow, compare, c) = zones[o].compare(zone)
            stat.append([o, c, len(missing), len(overflow)])

        # Create Default Dict and construct line
        s = "\r"
        d = defaultdict(lambda:31)
        d[0] = 32;d[1] = 33;d[2] = 31
        g = (d[i] for i in range(len(stat)))

        # Create Color
        for i,t in zip(g,sorted(range(len(stat)), key=lambda x: -stat[x][1])):
            stat[t].insert(1,i)

        for t in stat:
            s += "\x1B[34m%s\x1B[0m:\x1B[%sm%.3f\x1B[0m(%d/%d) "\
                    .__mod__(tuple(t))

        sys.stdout.write(s)

def main(pick, cur = None, tim = None, _slp = 5, device = None):
    """ Main Function for Module 
        
            @param pick The pickle filepath
            @param cur The selected zone or None
            @param tim Either the number before a clear or the number of takes
            @param _slp The Sleep Timer
            @param device The Device
        """
    global recr, slp
    slp = _slp
        
    if pick != None:
        # Get Zones
        try:
            zones = pickle.load(open(pick,"rb"))
        except IOError:
            # Create File
            with open(pick,"wb+"):
                pass
            zones = dict()
        except EOFError:
            # Just create an empty dict
            zones = dict()
    else:
        raise TypeError("pyWifiZone needs a Zone Pickle")

    zone = None
    if cur not in ["basic","short","inter","score",None]:
        try:
            zone = zones[cur]
        except:
            zone = Zone()

        # Create Zone or Update
        zones[cur] = updateZone(zone, tim, slp=slp)
        # Dump the data
        pickle.dump(zones, open(pick,"wb"))

    else:
        recr = 0 if tim is None else tim
        zone = Zone()

        if len(zones) == 0:
            print "You need to load some Zones"
            sys.exit(1)

        if cur == "inter":
            # This will Exit only on kill
            _interactive(zone, zones)

        # Register Kill Signal
        signal.signal(signal.SIGINT, _kill)
        if cur == "current":
            _current(zone, zones)
        elif cur == "short":
            _basic(zone, zones, True)
        elif cur == "score":
            _score(zone, zones)
        else:
            _basic(zone, zones)
