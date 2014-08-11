#!/bin/bash
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

_pywifi() 
{
    local cur prev opts rgx gtn
    COMPREPLY=()

    # First Command
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"
    gtn="${COMP_WORDS[@]:0:COMP_CWORD-1}"
    opts="--help --file --sleep --device --command --takes -h -f - s -d -c -t"

    case "$prev" in
	"--device" | "-d") opts=$(iwconfig 2>&1 | \
        sed -En "s/^([a-zA-Z0-9]+).*$/\1/p") 
        ;;
    "--help" | "-h") opts="" 
        ;;
    "--sleep" | "-s") opts=""
        ;;
    "--command" | "-c") opts="short basic inter score"
        ;;
    "--takes" | "-t") opts=""
        ;;
    "--file" | "-f") opts=$(compgen -A file "$cur")
        ;;
    *)

        rgx="s/($(echo -n "$gtn" | tr ' ' '\n' | sed -En "/^--/p" | \
            tr '\n' ' ' | \
            sed -E "s/[[:space:]]+/|/g" ))//g"
        opts=$(echo "$opts" | sed -E "$rgx")
        ;;
	esac

	COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
	return 0
}

complete -F _pywifi pywifi
