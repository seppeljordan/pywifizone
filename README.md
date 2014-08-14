## PyWifiZone

PyWifiZone measures wifi-footprints in different locations and tries to locate a
wifi device based on the data. This means you can locate yourself in a flat by 
just comparing the different wifi signals and strengths.

The Command Line Tool is named **pywifi** and installed into `/usr/bin/`

## Requirements

PyWifiZone needs the linux command **iwlist** and for full completion 
**iwconfig** as well as **sed** and a **bash** compatible shell.

## State

The current version is supposed to be stable. Note thought that there are no 
tests yet.

## Bugs reports

Please report bugs and feature requests at
https://github.com/baldulin/pywifizone/issues

## Manual

The manual is stored in **pywifi.7.gz** and is available after installation with

```
man pywifi
```

## Completion

With installation the autocompletion file **complete_pywifi.sh** will be 
installed into `/etc/bash_completion.d/`.
