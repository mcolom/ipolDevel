#!/bin/bash

# Very simple script to make backups
# Miguel Colom, 2016

backupsFolder="/home/ipol/backups"
snapshot=$(date +"snapshot_%Y-%q")
yearPeriod=$(date +"%Y-%q")

snapshotName=${backupsFolder}/${yearPeriod}/${snapshot}

backupFilename=$(date +"backup_%m-%d-%Y.tgz")
fullFilename=${backupsFolder}/${yearPeriod}/${backupFilename}

demo_binaries="/home/ipol/ipolDevel/ipol_demo/modules/demorunner/binaries"
shared_folder="/home/ipol/ipolDevel/shared_folder"

mkdir -p $backupsFolder/$yearPeriod
tar -g $snapshotName -czf $fullFilename --exclude=\"$shared_folder\" --exclude=\"$demo_binaries\" ~/ipolDevel

##############
# To restore a backup pipe a cat with all .tgz files into tar extract 
# command and specify a destination path (restore_folder)
# tar xvpzf tar_file1.tgz -g /dev/null --ignore-zeros -C restore_folder 
##############