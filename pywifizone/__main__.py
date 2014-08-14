#!/usr/bin/python
# -*- coding: utf-8 -*-
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

from wifi import *
from optparse import OptionParser

usage = "usage: %prog [options] arg"
parser = OptionParser(usage)
parser.add_option("-f", "--file", dest="filename", \
        help="read data from pickle File")
parser.add_option("-s", "--sleep", dest="sleep",\
        help="sleep timer in between measurements")
parser.add_option("-d", "--device", dest="device", help="device name")
parser.add_option("-c","--command", dest="command", \
        help="Command (basic [default], <zone>, short, inter, score)")
parser.add_option("-t","--takes", dest="takes", help="Take or reset counter")

(options, args) = parser.parse_args()

if options.filename == None:
    print "Need a pickle file [-f <file>]"
    sys.exit(1)

if options.command not in ["basic","short","inter","score",None]:
    if not options.takes > 0:
        print "Needs takes>0 for updating Zone \x1B[34m%s\x1B[0m [-t <takes>]"\
                % options.command

        sys.exit(2)
elif options.command == "basic":
    options.command = None

try:
    if options.takes != None:
        options.takes = int(options.takes)
except:
    print "Takes needs to be an integer >= 0 [-t <takes>]"
    sys.exit(3)

try:
    if options.sleep != None:
        options.sleep = float(options.sleep)

    if options.sleep <= 0:
        raise Exception("Greater Zero")
except:
    print "Sleep needs to be an integer >= 0 [-s <sleep>]"
    sys.exit(4)

main(pick = options.filename,
        cur = options.command,
        tim = options.takes,
        _slp = 5 if options.sleep is None else options.sleep,
        device = options.device
        )
