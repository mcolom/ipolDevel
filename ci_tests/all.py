#!/usr/bin/python
# -*- coding: utf-8 -*-

import time
import random
from subprocess import Popen, PIPE
import os

system_test = '/home/ipol/ipolDevel/ci_tests/system.py'
archive_test = '/home/ipol/ipolDevel/ipol_demo/modules/archive/test.py'
blobs_test = '/home/ipol/ipolDevel/ipol_demo/modules/blobs/test.py'
demoinfo_test = '/home/ipol/ipolDevel/ipol_demo/modules/demoinfo/test.py'
dispatcher_test = '/home/ipol/ipolDevel/ipol_demo/modules/dispatcher/test.py'
demorunner_test = '/home/ipol/ipolDevel/ipol_demo/modules/demorunner/test.py'

resources = '/home/ipol/ipolDevel/ci_tests/resources'
demorunners = '/home/ipol/ipolDevel/ipol_demo/modules/config_common/demorunners.xml'
shared_folder = '/home/ipol/ipolDevel/shared_folder'

tests = [system_test, demoinfo_test, blobs_test, archive_test, dispatcher_test, demorunner_test]


def start():
    """
    Start the script
    """
    try:
        while not can_execute():
            # Wait random time between 5 and 10 sec to try to execute the test again
            time.sleep(5 + random.random() * 5)

        run_tests()
    finally:
        os.remove('test.lock')


def can_execute():
    """
    Check if the test can be executed. Only 1 test can be executed simultaneously
    """
    if os.path.isfile('test.lock'):
        return False

    open('test.lock', 'w')
    return True


def run_tests():
    """
    Execute all the tests
    """
    for test in tests:
        # Print the tested module
        module_name = os.path.basename(os.path.split(test)[0]).title()
        if module_name == '': module_name = 'System'

        # Execute test
        process = Popen(['python', test, resources, demorunners, shared_folder], stdout=PIPE, stderr=PIPE)
        stdout, stderr = process.communicate()

        if process.returncode != 0:
            print "{} test failed:".format(module_name)
            print stderr
            print stdout
            exit(process.returncode)


start()
