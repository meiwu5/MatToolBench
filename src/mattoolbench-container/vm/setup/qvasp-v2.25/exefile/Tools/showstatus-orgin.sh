#!/bin/bash

#Write by : Yi,Wencai 
#Mail:yi.wencai@163.com
#Date:2014.06.21
#Modified by Yi,Wencai;2014.06.20
#Write it to show status of our job

qstat -u $USER

## or you could choose one of them as follow:

# top -n 2
# squeue -u $USER
# bjobs
