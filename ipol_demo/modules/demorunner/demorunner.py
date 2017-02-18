#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
This file implements the demo runner module,
which takes care of running an IPOL demo using web services
"""

# add lib path for import
import os.path, sys
sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), "Tools"))


import hashlib
from   datetime import datetime

import urllib2
from   timeit   import default_timer as timer
from   image    import thumbnail, image
from   misc     import prod
import PIL.ImageDraw

import threading
import cherrypy
import os
import json
import glob
import shutil
import time

import  run_demo_base
from    run_demo_base import RunDemoBase
from    run_demo_base import IPOLTimeoutError

import traceback


import subprocess
import errno
import logging


import urlparse
import os, shutil

from misc import ctime

import shutil
import stat
import urlparse
from os import path

import build

import tempfile
import time

from string import Template
from threading import Lock

class DemoRunner(object):
    """
    This class implements Web services to run IPOL demos
    """
    @staticmethod
    def mkdir_p(path):
        """
        Implement the UNIX shell command "mkdir -p"
        with given path as parameter.
        """
        created = 'false'
        try:
            os.makedirs(path)
            created = 'true'
        except OSError as exc:
            if exc.errno == errno.EEXIST and os.path.isdir(path):
                pass
            else:
                raise

        return created

    def init_logging(self):
        """
        Initialize the error logs of the module.
        """
        logger = logging.getLogger("core_log")
        logger.setLevel(logging.ERROR)
        handler = logging.FileHandler(self.log_file)
        formatter = logging.Formatter('%(asctime)s ERROR in %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger

    def write_log(self, function_name, message):
        """
        Write an error log in the logs_dir defined in proxy.conf
        """
        log_string = "{}: {}".format(function_name, message)
        #
        self.logger.error(log_string)


    def __init__(self):
        """
        Initialize DemoRunner
        """
        self.lock = Lock()

        base_dir = os.path.dirname(os.path.realpath(__file__))
        self.share_running_dir = cherrypy.config['share.running.dir']
        self.main_bin_dir = os.path.join(base_dir, cherrypy.config['main.bin.dir'])
        self.main_log_dir = cherrypy.config['main.log.dir']
        self.main_log_name = cherrypy.config['main.log.name']
        self.share_demoExtras_dir = cherrypy.config['share.demoExtras.dir']
        self.MATLAB_path = cherrypy.config['demo.matlab_path']
        self.log_file = os.path.join(self.main_log_dir, self.main_log_name)

        self.png_compresslevel = 1
        self.stack_depth = 0

        self.mkdir_p(self.main_bin_dir)
        self.mkdir_p(self.main_log_dir)

        self.logger = self.init_logging()

        if not os.path.isdir(self.share_running_dir):
            error_message = "The folder does not exist: " + self.share_running_dir
            print error_message
            self.write_log("__init__", error_message)


            #####
            # web utilities
            #####

    @cherrypy.expose
    def index(self):
        """
        HTML presentation page
        """
        return ("This is the IPOL DemoRunner module")

    @cherrypy.expose
    def ping(self):
        """
        Ping service: answer with a PONG.
        """
        data = {}
        data["status"] = "OK"
        data["ping"] = "pong"
        return json.dumps(data)

    @cherrypy.expose
    def shutdown(self):
        """
        Shutdown the module.
        """
        data = {}
        data["status"] = "KO"
        try:
            cherrypy.engine.exit()
            data["status"] = "OK"
        except Exception as ex:
            self.write_log("shutdown", str(ex))
        return json.dumps(data)

    @cherrypy.expose
    def get_load_state(self):
        """
        Returns the CPU load of the machine
        """
        data = {}
        data["status"] = "KO"
        try:
            mpstat_result = subprocess.check_output(['mpstat'])
            CPU_information = str(mpstat_result).split()
            CPU_information = CPU_information[-1].replace(",", ".")
            data["CPU"] = float(CPU_information)
            data["status"] = "OK"
        except Exception as ex:
            self.write_log("get_load_state", str(ex))
        return json.dumps(data)

        # ---------------------------------------------------------------------------

    @cherrypy.expose
    def default(self, attr):
        """
        Default method invoked when asked for non-existing service.
        """
        data = {}
        data["status"] = "KO"
        data["message"] = "Unknown service '{}'".format(attr)
        return json.dumps(data)

    # -----------------------------------------------------------------------------
    @cherrypy.expose
    def get_workload(self):
        """
        Return the workload of this DR
        """
        data = {}
        data["status"] = "OK"
        # Command to obtain the workload for a specific user
        cmd = "ps -eo %U,%C| grep ipol | cut -d \",\" -f2"
        try:
            # Get the workload
            processes, error = subprocess.Popen(cmd + " &",
                                                shell=True,
                                                executable="/bin/bash",
                                                stdout=subprocess.PIPE,
                                                stderr=subprocess.PIPE).communicate()
            # Get the number of cores
            nproc, error = subprocess.Popen("nproc &",
                                            shell=True,
                                            executable="/bin/bash",
                                            stdout=subprocess.PIPE,
                                            stderr=subprocess.PIPE).communicate()
            total = 0.0
            # Get the total workload
            for process in processes.split("\n"):
                if process != "":
                    total += float(process)
            data['workload'] = total / float(nproc)
        except Exception as ex:
            data["status"] = "KO"
            self.logger.exception("Could not get workload from the DR")
            print "Could not get workload from the DR -", ex

        return json.dumps(data)

    def make_karl(self, path_for_the_compilation, ddl_build):
        """
        program build/update
        """
        self.write_log("make_karl", \
          "Using deprecated make_karl function to compile - {}".\
            format(path_for_the_compilation))

        print "make begin"
        total_start = time.time()
        make_info = ""

        zip_filename = urlparse.urlsplit(ddl_build['url']).path.split('/')[-1]
        src_dir_name = ddl_build['srcdir']

        dl_dir = os.path.join(path_for_the_compilation, 'dl/')
        scripts_dir = os.path.join(path_for_the_compilation, 'scripts/')
        log_file = os.path.join(path_for_the_compilation, 'build.log')
        src_dir = os.path.join(path_for_the_compilation, 'src/')
        bin_dir = os.path.join(path_for_the_compilation, 'bin/')
        src_path = os.path.join(src_dir, src_dir_name)

        self.mkdir_p(dl_dir)
        tgz_file = path.join(dl_dir, zip_filename)

        print "Initing the make in ", path_for_the_compilation
        # get the latest source archive
        try:
            build.download(ddl_build['url'], tgz_file)
        except Exception as ex:
            self.write_log("make", "Failed to download the sources: {}".format(tgz_file))
            raise

        rebuild_needed = False

        ## test if the dest file is missing, or too old, for each program to build
        if 'binaries' in ddl_build:
            programs = ddl_build['binaries']
            for program in programs:
                print "build ", program
                # use first binary name to check time
                prog_filename = program[1]
                try:
                    prog_file = path.join(bin_dir, os.path.basename(prog_filename))  ### AQUI GUARDA EL BINARIO AL FINAL
                    if os.path.basename(prog_filename) == '' and len(program) == 3:
                        prog_file = path.join(bin_dir, program[2])
                    if not (path.isfile(prog_file)) or (ctime(tgz_file) > ctime(prog_file)):
                        rebuild_needed = True
                except Exception as ex:
                    self.logger.exception("make")
                    raise

        # test timestamp for scripts too
        if 'scripts' in ddl_build.keys():
            for script in ddl_build['scripts']:
                try:
                    script_file = path.join(scripts_dir, script[1])
                    if os.path.basename(script[1]) == '' and len(script) == 3:
                        script_file = path.join(scripts_dir, script[1], script[2])
                    if not (path.isfile(script_file)) or (ctime(tgz_file) > ctime(script_file)):
                        rebuild_needed = True
                except Exception as ex:
                    self.logger.exception("make")
                    raise

        # --- build
        if not (rebuild_needed):
            make_info += "no rebuild needed "
            print "no rebuild needed for demo ", path_for_the_compilation
        else:

            print "Extracting code for demo ", path_for_the_compilation
            # extract the archive
            start = time.time()  # 040404

            if path.isdir(src_dir):
                shutil.rmtree(src_dir)
            self.mkdir_p(src_dir)

            build.extract(tgz_file, src_dir)
            make_info += "extracting archive: " + tgz_file + " sec.; ".format(time.time() - start)
            print make_info

            print "creating bin_dir"
            if path.isdir(bin_dir):
                shutil.rmtree(bin_dir)
            self.mkdir_p(bin_dir)

            print "creating scripts dir"
            if path.isdir(scripts_dir):
                shutil.rmtree(scripts_dir)
            self.mkdir_p(scripts_dir)

            ## Execute make or cmake
            start = time.time()

            if ('build_type' in ddl_build.keys()) and \
                    (ddl_build['build_type'].upper() == 'cmake'.upper()):
                self.do_cmake_karl(bin_dir, ddl_build, log_file, programs, src_path)
            else:
                self.do_make_karl(bin_dir, ddl_build, log_file, programs, src_path)

            # if build_type is 'script', just execute this part
            if 'scripts' in ddl_build.keys():
                self.do_scripts_karl(ddl_build, scripts_dir, src_path)# prepare_cmake can fix some options before configuration

            if ('post_build' in ddl_build.keys()):
                print 'post_build command:', ddl_build['post_build']
                build.run(ddl_build['post_build'],
                          stdout=log_file, cwd=src_path)

            # cleanup the source dir
            shutil.rmtree(src_dir)
            make_info += "build: {0} sec.; ".format(time.time() - start)

        make_info += "total elapsed time: {0} sec.".format(time.time() - total_start)
        print "make end"

        return make_info

    def make_new(self, path_for_the_compilation, ddl_builds):
        """
        program build/update
        """
        dl_dir = os.path.join(path_for_the_compilation, 'dl/')
        src_dir = os.path.join(path_for_the_compilation, 'src/')
        bin_dir = os.path.join(path_for_the_compilation, 'bin/')
        log_file = os.path.join(path_for_the_compilation, 'build.log')
        
        try:
            # Clear src/ folder
            if os.path.isdir(src_dir):
                shutil.rmtree(src_dir)
            self.mkdir_p(src_dir)
            self.mkdir_p(dl_dir)
            self.mkdir_p(bin_dir)
        except Exception:
            self.logger.exception("Directory operation failed")
            raise

        for build_item in ddl_builds.items():
            # Move to the compilation directory, in case the
            # instructions in the move directive have changed it
            os.chdir(src_dir)
            
            build_item = build_item[1]
            # Read DDL
            url = build_item['url']
            files_to_move = build_item['move']
            construct = build_item['construct'] if 'construct' in build_item else None

            zip_filename = urlparse.urlsplit(url).path.split('/')[-1]
            tgz_file = path.join(dl_dir, zip_filename)

            # Get files to move path
            files_path = []
            for file in files_to_move.split(","):
                files_path.append(path.join(bin_dir,os.path.basename(file.strip())))


            try:
                # Download
                extract_needed = build.download(url, tgz_file)

                # Check if a rebuild is nedded
                if extract_needed or not self.all_files_exist(files_path):
                    # Extract source code
                    build.extract(tgz_file, src_dir)

                    if construct is not None:
                        # Execute the construct
                        build.run(construct, log_file, cwd=src_dir)

                    # Move files
                    for file_to_move in files_to_move.split(","):
                        # Remove possible white spaces
                        file_to_move = file_to_move.strip()
                        #
                        path_from = path.join(src_dir,file_to_move)
                        path_to = path.join(bin_dir, os.path.basename(file_to_move))
                        
                        print "Moving {} --> {}".\
                              format(path_from, path_to)
                        
                        try:
                            shutil.move(path_from, path_to)
                        except (IOError, OSError):
                            # If can't move, write in the log file, so
                            # the user can see it
                            f = open(log_file, 'w')
                            f.write("Failed to move {} --> {}".\
                              format(path_from, path_to))
                            f.close()
                            raise                            
            except Exception:
                self.logger.exception("Build failed")
                raise


    def all_files_exist(self, files):
        '''
        Checks if all given file names exist
        '''
        return all([os.path.isfile(f) or os.path.isdir(f) \
          for f in files])


    def do_scripts_karl(self, ddl_build, scripts_dir, src_path):
        self.write_log("do_cmake_karl", \
          "Using deprecated do_cmake_karl function to compile - {}".\
            format(src_path))

        print ddl_build['scripts']
        # Move scripts to the scripts dir
        for script in ddl_build['scripts']:
            print "moving ", path.join(src_path, script[0], script[1]), " to ", scripts_dir
            new_file = path.join(scripts_dir, script[1])

            if os.path.exists(new_file):
                if path.isfile(new_file):
                    os.remove(new_file)
                else:
                    os.chmod(new_file, stat.S_IRWXU)
                    shutil.rmtree(new_file)
            shutil.move(path.join(src_path, script[0], script[1]), scripts_dir)
            # Give exec permission to the script
            os.chmod(new_file, stat.S_IREAD | stat.S_IEXEC)


    # This function is deprecated and should be totally removed when no
    # demo is using the old syntax.
    def do_make_karl(self, bin_dir, ddl_build, log_file, programs, src_path):
        self.write_log("do_make_karl", \
          "Using deprecated do_make_karl function to compile - {}".\
            format(src_path))

        if ('build_type' in ddl_build.keys()) and \
                (ddl_build['build_type'].upper() == 'make'.upper()):
            # ----- MAKE build
            print "using MAKE"

            # prepare_cmake can fix some options before configuration
            if ('prepare_make' in ddl_build.keys()):
                print 'prepare_make :', ddl_build['prepare_make']
                build.run(ddl_build['prepare_make'], stdout=log_file, cwd=src_path)

            moves = []

            # build the programs for make
            for program in programs:
                target = program[1]
                make_C_dir = path.join(src_path, program[0])
                target_path = path.join(make_C_dir, target)
                bins_to_move = program[1:] if len(program) >= 2 else [target]

                # build
                if os.path.isdir(target_path):
                    cmd = "make %s -C %s" % (ddl_build['flags'], make_C_dir)
                    # print "CASO 1, cmd={}".format(cmd)
                else:
                    cmd = "make %s -C %s %s" % (ddl_build['flags'], make_C_dir, target)
                    # print "CASO 2, cmd={}".format(cmd)

                print cmd
                build.run(cmd, stdout=log_file)

                if os.path.isdir(target_path):
                    print "copying all files in bin dir from:", target_path
                    # copy all files to bin dir
                    for file_name in os.listdir(target_path):
                        full_file_name = os.path.join(target_path, file_name)
                        if (os.path.isfile(full_file_name)):
                            print "{0}; ".format(file_name),
                            shutil.copy(full_file_name, bin_dir)
                else:
                    # copy binary to bin dir
                    print "{0}-->{1}".format(target_path, bin_dir)

                    # shutil.copy(target_path, bin_dir)
                    for bin_to_move in bins_to_move:
                        # print "\n\n*******************"
                        # print "target={}".format(target)
                        # print "make_C_dir={}".format(make_C_dir)
                        # print "target_path=", target_path
                        # print "bin_to_move=", bin_to_move
                        # print "*******************\n\n"
                        moves.append((os.path.join(make_C_dir, bin_to_move), bin_dir))
                        # shutil.copy(file_from, bin_dir)

            for move in moves:
                print "COPY {} --> {}".format(move[0], move[1])
                shutil.copy(move[0], move[1])

    # This function is deprecated and should be totally removed when no
    # demo is using the old syntax.
    def do_cmake_karl(self, bin_dir, ddl_build, log_file, programs, src_path):
        self.write_log("do_cmake_karl", \
          "Using deprecated do_cmake_karl function to compile - {}".\
            format(src_path))
        
        print "using CMAKE"
        # Run cmake first:
        # create temporary build dir IPOL_xxx_build
        build_dir = path.join(src_path, "__IPOL_build__")
        self.mkdir_p(build_dir)
        # prepare_cmake can fix some options before configuration
        if ('prepare_cmake' in ddl_build.keys()):
            print 'prepare_cmake :', ddl_build['prepare_cmake']
            build.run(ddl_build['prepare_cmake'], stdout=log_file, cwd=src_path)
        print "..."
        # set release mode by default, other options could be added
        if ('cmake_flags' in ddl_build.keys()):
            cmake_flags = ddl_build['cmake_flags']
        else:
            cmake_flags = ''
        build.run("cmake -D CMAKE_BUILD_TYPE:string=Release " + cmake_flags + " " + src_path,
                  stdout=log_file, cwd=build_dir)
        # build
        build.run("make %s " % (ddl_build['flags']), stdout=log_file, cwd=build_dir)
        ## copy binaries
        for program in programs:
            prog_path = path.join(build_dir, program[0])
            target = path.join(prog_path, program[1])

            if os.path.isdir(target):
                print "copying all files in bin dir"
                # copy all files to bin dir
                # src_files = os.listdir(target)
                for file_name in src_files:
                    full_file_name = os.path.join(target, file_name)
                if (os.path.isfile(full_file_name)):
                    print "{0}; ".format(file_name),
                    shutil.copy(full_file_name, bin_dir)
                print ''
            else:
                # copy binary to bin dir
                print "{0}-->{1}".format(target, bin_dir)
                shutil.copy(target, bin_dir)

    @cherrypy.expose
    def ensure_compilation(self, demo_id, ddl_build):
        """
        Ensures that the source codes of the given demo are compiled and
        moved correcty.
        """
        print "\nDEMO ID " + demo_id + " is in ensure_compilation\n"
        ddl_build = json.loads(ddl_build)

        path_for_the_compilation = os.path.join(self.main_bin_dir, demo_id)
        self.mkdir_p(path_for_the_compilation)

        # we should have a dict or a list of dict
        if isinstance(ddl_build, dict):
            builds = [ddl_build]
        else:
            builds = ddl_build
        
        for build_params in builds:
            try:
                print ddl_build
                print type(ddl_build)
                if 'build1' in ddl_build:
                    make_info = self.make_new(path_for_the_compilation, build_params)
                else:
                    # [ToDo] [Miguel] This function is deprecated. It
                    # should be totally removed when no demo is
                    # using the old compilation syntax.
                    # And make_new renamed.
                    make_info = self.make_karl(path_for_the_compilation, build_params)
                print make_info

                data = {}
                data['status'] = "OK"
                data['message'] = "Build of demo {0} OK".format(demo_id)
                data['info'] = make_info
            except urllib2.HTTPError as e:
                print "HTTPError"
                self.logger.exception("ensure_compilation - HTTPError")
                data = {}
                data['status'] = 'KO'                
                data['message'] = "{}, build_params: {}".format(str(e), str(build_params))
                return json.dumps(data)                
            except Exception as e:
                print "Build failed with exception " + str(e) + " in demo " + demo_id
                self.logger.exception("ensure_compilation")
                
                log_file = os.path.join(path_for_the_compilation, 'build.log')
                #
                lines = ""
                if os.path.isfile(log_file):
                    with open(log_file) as f:
                        lines = f.readlines()                
                data = {}
                data['status'] = 'KO'                
                data['message'] = "Build for demo {0} failed".format(demo_id)
                data['buildlog'] = lines
                return json.dumps(data)

        return json.dumps(data)

    # ---------------------------------------------------------------------------
    # Algorithm runner
    # ---------------------------------------------------------------------------
    def run_algo(self, demo_id, work_dir, bin_path, ddl_run, params, res_data, timeout):
        """
        the core algo runner
        """
        print "\n\n----- run_algo begin -----\n\n"
        rd = run_demo_base.RunDemoBase(bin_path, work_dir, self.logger,timeout)
        rd.set_algo_params(params)
        rd.set_algo_info(res_data['algo_info'])
        rd.set_MATLAB_path(self.MATLAB_path)
        rd.set_demo_id(demo_id)
        rd.set_commands(ddl_run)

        rd.set_share_demoExtras_dirs(self.share_demoExtras_dir, demo_id)

        if isinstance(ddl_run, list): #Checks if the run parameter in the DDL have more than one line
            rd.run_algorithm_karl()
        else:
            cmd = self.variable_substitution(ddl_run,demo_id, params)
            rd.run_algorithm(cmd, self.lock)

        res_data['params'] = rd.get_algo_params()
        res_data['algo_info'] = rd.get_algo_info()
        print "----- run_algo end -----"

    def variable_substitution(self, ddl_run, demo_id, params):
        """
        Replace the variables with its values and return the command to be executed
        """
        params["demoextras"] = os.path.join(self.share_demoExtras_dir, demo_id)
        params["matlab_path"] = self.MATLAB_path
        params["bin"] = self.get_bin_dir(demo_id)
        return Template(ddl_run).substitute(**params)

    def get_bin_dir(self, demo_id):
        '''
        Returns the directory with the peer-reviewed author programs
        '''
        return os.path.join(self.main_bin_dir, demo_id, 'bin/')
        

    def read_workdir_file(self, work_dir, filename):
        '''
        Reads a text files from the working directory
        '''
        full_file = os.path.join(work_dir, filename)
        lines = ""
        if os.path.isfile(full_file):
            with open(full_file) as f:
                lines = f.readlines()
        return lines


    @cherrypy.expose
    def exec_and_wait(self, demo_id, key, params, ddl_run, ddl_config=None, timeout=60):
        '''
        Called by the Core to run the algorithm
        '''
        print "#### run demo ####"
        print "demo_id = ", demo_id
        ddl_run = json.loads(ddl_run)
        print "ddl_run = ", ddl_run
        params = json.loads(params)
        print "params = ", params

        path_with_the_binaries = os.path.join(self.main_bin_dir, demo_id + "/")
        print "path_with_the_binaries = ", path_with_the_binaries
        work_dir = os.path.join(self.share_running_dir, demo_id + '/' + key + "/")
        print "run dir = ", work_dir

        res_data = {}
        res_data["key"] = key
        res_data['params'] = params
        res_data['status'] = 'KO'
        res_data['algo_info'] = {}

        # TODO:this code will be moved to the CORE
        # save parameters as a params.json file
        try:
            with open(os.path.join(work_dir, "params.json"), "w") as resfile:
                json.dump(params, resfile)
        except Exception as ex:
            self.logger.exception("Save params.json, demo_id={}".format(demo_id))
            print "Failed to save params.json file"
            res_data['status'] = 'KO'
            res_data['error'] = 'Save params.json'
            return json.dumps(res_data)

        # run the algorithm
        try:
            run_time = time.time()

            print "Demoid: ", demo_id

            timeout = float(timeout)
            timeout = min(timeout, 10*60) # A maximum of 10 min, regardless the config
            self.run_algo(demo_id, work_dir, path_with_the_binaries, ddl_run, params, res_data, timeout)

            # re-read the config in case it changed during the execution
            res_data['algo_info']['run_time'] = time.time() - run_time
            res_data['status'] = 'OK'
        except IPOLTimeoutError:
            self.write_log("exec_and_wait", "IPOLTimeoutError, demo_id={}".format(demo_id))
            res_data['status'] = 'KO'
            res_data['error'] = 'IPOLTimeoutError'
            res_data['algo_info']['status'] = 'RuntimeError, Timeout={} s'.format(timeout)
            print res_data
            return json.dumps(res_data)
        except RuntimeError as e:            
            self.write_log("exec_and_wait", "RuntimeError, demo_id={}".format(demo_id))
    
            # Read stderr and stdout
            stderr_lines = self.read_workdir_file(work_dir, "stderr.txt")
            stdout_lines = self.read_workdir_file(work_dir, "stdout.txt")
                        
            # Put them in the message for the web interface
            res_data['algo_info']['status'] = 'RuntimeError, \
stderr={}, stdout={}'.format(stderr_lines, stdout_lines)

            res_data['status'] = 'KO'
            res_data['error'] = str(e)
            print res_data
            return json.dumps(res_data)

        except OSError as ex:
            error_str = "{} - errno={}, filename={}, ddl_run={}".format(str(ex), ex.errno, ex.filename, ddl_run)
            self.write_log("exec_and_wait", "OSError, demo_id={}, {}".format(demo_id, error_str))
            res_data['status'] = 'KO'
            res_data['algo_info']['status'] = error_str
            res_data['error'] = error_str
            print res_data
            return json.dumps(res_data)
        except KeyError as ex:
            error_str = "KeyError. Hint: variable not defined? - {}, ddl_run={}".format(str(ex), ddl_run)
            self.write_log("exec_and_wait", "OSError, demo_id={}, {}".format(demo_id, error_str))
            res_data['status'] = 'KO'
            res_data['algo_info']['status'] = error_str
            res_data['error'] = error_str
            print res_data
            return json.dumps(res_data)
        except Exception as e:
            self.logger.exception("Uncatched Exception, demo_id={}".format(demo_id))
            res_data['status'] = 'KO'
            res_data['error'] = 'Error: {}'.format(e)
            print res_data
            return json.dumps(res_data)


        # TODO:this code will be moved to the CORE
        # get back parameters
        try:
            with open(os.path.join(work_dir, "params.json")) as resfile:
                res_data['params'] = json.load(resfile)
        except Exception as ex:
            print "Failed to read params.json file"
            self.logger.exception("exec_and_wait can't read params.json, demo_id={}".format(demo_id))
            res_data['status'] = 'KO'
            res_data['error'] = 'Read params.json'
            return json.dumps(res_data)

        # check if new config fields
        if ddl_config != None:
            ddl_config = json.loads(ddl_config)
            if 'info_from_file' in ddl_config.keys():
                for info in ddl_config['info_from_file']:
                    print "*** ", info
                    filename = ddl_config['info_from_file'][info]
                    try:
                        f = open(os.path.join(work_dir, filename))
                        print "open ok"
                        file_lines = f.read().splitlines()
                        print file_lines
                        # remove empty lines and replace new lines with ' | '
                        new_string = " | ".join([ll.rstrip() for ll in file_lines if ll.strip()])
                        print new_string
                        res_data['algo_info'][info] = new_string
                        f.close()
                    except Exception as e:
                        self.logger.exception("DDL - Failed to get info from {}".format(os.path.join(work_dir, filename)))
                        print "failed to get info ", info, " from file ", os.path.join(work_dir, filename)
                        print "Exception ", e

        print res_data
        return json.dumps(res_data)
