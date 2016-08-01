#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
Main function
Load from the blobs configuration file
Create the cherrypy server
"""

import cherrypy
import os
import os.path
import sys
from demorunner import DemoRunner
from error import print_usage_function

def CORS(): 
  cherrypy.response.headers["Access-Control-Allow-Origin"] = "*" # mean: CORS to 

if __name__ == '__main__':

    cherrypy.tools.CORS = cherrypy.Tool('before_handler', CORS) 

    if len(sys.argv) == 2 and os.path.isfile(sys.argv[1]):
        VALUE = sys.argv[1]
    else:
        VALUE="demorunner.conf"

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    CONF_FILE = os.path.join(BASE_DIR, VALUE)

    cherrypy.config.update(CONF_FILE)

    RUNNING = cherrypy.config['running.dir']

    CONF = {
        '/' : {
            'tools.staticdir.root': os.getcwd(),
        },
        '/run': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': RUNNING
        }
    }

    cherrypy.config.update(CONF)

    APP = cherrypy.tree.mount(DemoRunner(), '/', CONF)
    APP.merge(CONF_FILE)

    if hasattr(cherrypy.engine, "signal_handler"):
        cherrypy.engine.signal_handler.subscribe()
    if hasattr(cherrypy.engine, "console_control_handler"):
        cherrypy.engine.console_control_handler.subscribe()
    cherrypy.engine.start()
    cherrypy.engine.block()