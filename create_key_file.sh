#!/usr/bin/env bash

eagle &
sleep 1
xdotool search --name 'EAGLE License' key Right key Return
sleep 1
xdotool search --name "Warning" key Return
