#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
This file implements the demo runner module,
which takes care of running an IPOL demo using web services
"""

# add lib path for import
import os.path, sys
sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), "../../lib"))
sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), "../.."))


import hashlib
from   datetime import datetime
from   random   import random
import urllib
from   timeit   import default_timer as timer
from   image    import thumbnail, image
from   misc     import prod

import threading
import cherrypy
import build_demo_base
import os
import json
import glob
import shutil
import time

import  run_demo_base
from    run_demo_base import RunDemoBase
from    run_demo_base import IPOLTimeoutError


class DemoRunner(object):
    """
    This class implements Web services to run IPOL demos
    """
    def __init__(self):
        """
        Initialize DemoRunner
        """
        self.running_dir = cherrypy.config['running.dir']
        self.current_directory = os.getcwd()
        self.server_address=  'http://{0}:{1}'.format(
                                  cherrypy.config['server.socket_host'],
                                  cherrypy.config['server.socket_port'])

    #---------------------------------------------------------------------------
    @cherrypy.expose
    def default(self, attr):
        """
        Default method invoked when asked for non-existing service.
        """
        data = {}
        data["status"] = "KO"
        data["message"] = "Unknown service '{}'".format(attr)
        return json.dumps(data)

    #---------------------------------------------------------------------------
    @cherrypy.expose
    def init_demo(self, demo_id, ddl_build):
        """
        Check if a demo is already compiled, if not compiles it
        :param demo_id:   id demo
        :param ddl_build: build section of the ddl json 
        """
        print "#### init_demo ####"
        result = self.check_build(demo_id,ddl_build)
        print "result is ",result
        return json.dumps(result)

    #---------------------------------------------------------------------------
    def check_build(self, demo_id, ddl_build):
        """
            rebuild demo from source code if required
        """

        res_data = {}

        # reload demo description
        demo_path = os.path.join(self.current_directory,\
                                 self.running_dir,\
                                 demo_id)
        
        # parse stringified json
        print "ddl_build = ", ddl_build
        ddl_build = json.loads(ddl_build)
        print "ddl_build = ", ddl_build

        print "---- check_build demo: {0:10}".format(demo_id),
        # we should have a dict or a list of dict
        if isinstance(ddl_build,dict):
            builds = [ ddl_build ]
        else:
            builds = ddl_build
        first_build = True
        for build_params in builds:
            bd = build_demo_base.BuildDemoBase( demo_path)
            bd.set_params(build_params)
            cherrypy.log("building", context='SETUP/%s' % demo_id,
                        traceback=False)
            try:
                make_info = bd.make(first_build)
                first_build=False
                res_data["status"]  = "OK"
                res_data["message"] = "Build for demo {0} checked".format(demo_id)
                res_data["info"]    = make_info
            except Exception as e:
                print "Build failed with exception ",e
                cherrypy.log("build failed (see the build log)",
                                context='SETUP/%s' % demo_id,
                                traceback=False)
                res_data["status"] = "KO"
                res_data["message"] = "Build for demo {0} failed".format(demo_id)
                return res_data
            
        print ""
        return res_data

    #---------------------------------------------------------------------------
    def WorkDir(self,demo_id,key):
        return os.path.join(    self.current_directory,\
                                self.running_dir,\
                                demo_id,\
                                'tmp',\
                                key+'/')

    #---------------------------------------------------------------------------
    def WorkUrl(self,demo_id,key):
        return os.path.join(    self.server_address,\
                                self.running_dir,\
                                demo_id,\
                                'tmp',\
                                key+'/')

    #---------------------------------------------------------------------------
    def BaseDir(self,demo_id,key):
        return os.path.join(    self.current_directory,\
                                self.running_dir,\
                                demo_id+'/')

    #---------------------------------------------------------------------------
    #
    # KEY MANAGEMENT
    #
    def get_new_key(self, demo_id, key=None):
        """
        create a key if needed, and the key-related attributes
        """
        if key is None:
            keygen = hashlib.md5()
            seeds = [cherrypy.request.remote.ip,
                     # use port to improve discrimination
                     # for proxied or NAT clients
                     cherrypy.request.remote.port,
                     datetime.now(),
                     random()]
            for seed in seeds:
                keygen.update(str(seed))
            key = keygen.hexdigest().upper()

        # check key
        if not (key and key.isalnum()):
            # HTTP Bad Request
            raise cherrypy.HTTPError(400, "The key is invalid")

        # reload demo description
        work_dir = self.WorkDir(demo_id,key)
        if not os.path.isdir(work_dir):
            os.makedirs(work_dir)

        return key
    

    #
    # INPUT HANDLING TOOLS
    #

    #---------------------------------------------------------------------------
    def save_image(self, im, fullpath):
        '''
        Save image object given full path
        '''
        im.save(fullpath)


    #---------------------------------------------------------------------------
    def need_convert_or_resize(self, im, input_info):
        '''
        Convert and resize an image object
        '''
        
        mode_kw = {'1x8i' : 'L',
                    '3x8i' : 'RGB'}
        # check max size
        max_pixels = eval(str(input_info['max_pixels']))

        return  im.im.mode != mode_kw[input_info['dtype']] or \
                prod(im.size) > max_pixels

    #---------------------------------------------------------------------------
    def convert_and_resize(self, im, input_info):
        '''
        Convert and resize an image object
        '''
        im.convert(input_info['dtype'])
        print "im.im.mode = ",im.im.mode
        # check max size
        max_pixels = eval(str(input_info['max_pixels']))
        resize = prod(im.size) > max_pixels
        if resize:
            cherrypy.log("input resize")
            im.resize(max_pixels)

    #---------------------------------------------------------------------------
    def process_inputs(self, demo_id, key, inputs_desc,crop_info, res_data):
        """
        pre-process the input data
        we suppose that config has been initialized, and save the dimensions
        of each converted image in self.cfg['meta']['input$i_size_{x,y}']
        """
        print "#### process_inputs ####"
        start = timer()
        msg = None
        ##self.max_width = 0
        ##self.max_height = 0
        nb_inputs = len(inputs_desc)
        work_dir = self.WorkDir(demo_id,key)
        
        for i in range(nb_inputs):
          # check the input type
          input_desc = inputs_desc[i]
          # find files starting with input_%i
          input_files = glob.glob(os.path.join(work_dir,'input_%i' % i+'.*'))
          
          if input_desc['type']=='image':
            # we deal with an image, go on ...
            print "Processing input ",i
            if len(input_files)!=1:
              # problem here
              raise cherrypy.HTTPError(400, "Wrong number of inputs for an image")
            else:
              # open the file as an image
              try:
                  im = image(input_files[0])
              except IOError:
                print "failed to read image " + input_files[0]
                raise cherrypy.HTTPError(400, # Bad Request
                                         "Bad input file")

            
            #-----------------------------
            # Save the original file as PNG
            # todo: why save original image as PNG??
            #
            # Do a check before security attempting copy.
            # If the check fails, do a save instead
            if  im.im.format != "PNG" or \
                im.size[0] > 20000 or im.size[1] > 20000 or \
                len(im.im.getbands()) > 4:
              # Save as PNG (slow)
              self.save_image(im, os.path.join(work_dir,'input_%i.orig.png' % i))
              # delete the original
              os.remove(input_files[0])
            else:
              # Move file (fast)
              shutil.move(input_files[0],
                          os.path.join(work_dir,'input_%i.orig.png' % i))

            
            #-----------------------------
            # convert to the expected input format: TODO: do it if needed ...
            
            # crop first if available
            crop_res = self.crop_input(i, demo_id, key, inputs_desc, crop_info)
            res_data['info'] += crop_res['info']
            if crop_res['status']=="OK":
                im_converted = image(crop_res['filename'])
                im_converted_filename = 'input_%i.crop.png' % i
            else:
                im_converted = im.clone()
                im_converted_filename = 'input_%i.orig.png' % i
            
            if self.need_convert_or_resize(im_converted,input_desc):
                print "need convertion or resize, input description: ", input_desc
                self.convert_and_resize(im_converted,input_desc)
                # save a web viewable copy
                im_converted.save(os.path.join(work_dir,'input_%i.png' % i))
            else:
                # just create a symbolic link  
                os.symlink(im_converted_filename,\
                           os.path.join(work_dir,'input_%i.png' % i))
                
            ext = input_desc['ext']
            # why saving a copy of the converted image in non-png format ?
            ## save a working copy:
            #if ext != ".png":
                ## Problem with PIL or our image class: this call seems to be
                ## problematic when saving PGM files. Not reentrant?? In any
                ## case, avoid calling it from a thread.
                ##threads.append(threading.Thread(target=self.save_image,
                ##               args = (im_converted, self.work_dir + 'input_%i' % i + ext))
                #self.save_image(im_converted, self.work_dir + 'input_%i' % i + ext)


            if im.size != im_converted.size:
                msg = "The image has been resized for a reduced computation time."
                print msg,": ", im.size, "-->", im_converted.size
            #self.max_width  = max(self.max_width,im_converted.size[0])
            #self.max_height = max(self.max_height,im_converted.size[1])
            #self.cfg['meta']['input%i_size_x'%i] = im_converted.size[0]
            #self.cfg['meta']['input%i_size_y'%i] = im_converted.size[1]
          # end if type is image
          else:
            # check if we have a representing image to display
            if len(input_files)>1:
              # the number of input files should be 2...
              # for the moment, only check for png file
              png_file = os.path.join(work_dir,'input_%i.png' % i)
              #if png_file in input_files:
                ## save in configuration the information to allow its display
                #self.cfg['meta']['input%i_has_image'%i] = True
        # end for i in range(nb_inputs)
        
        # for compatibility with previous system, create input_0.sel.png
        # as symbolic link
        os.symlink('input_0.png', os.path.join(work_dir,'input_0.sel.png'))
        
        end=timer()
        res_data["info"] += " process_inputs() took: {0} sec.;".format(end-start)
        
        return msg


    #---------------------------------------------------------------------------
    @cherrypy.expose
    def input_upload(self, **kwargs):
        """
        use the uploaded input files
        file_0, file_1, ... are the input files
        demo_id   id of the current demo
        ddl_input is the input section of the demo description
        """
        
        print "#### input_upload ####"
        # we need a unique key for the execution
        demo_id = kwargs['demo_id']
        key = self.get_new_key(demo_id)
        work_dir = self.WorkDir(demo_id,key)
        inputs_desc = json.loads(kwargs['ddl_input'])
        nb_inputs = len(inputs_desc)
        
        for i in range(nb_inputs):
          file_up = kwargs['file_%i' % i]
          
          if file_up.filename == '':
            if  not('required' in inputs_desc[i].keys()) or \
                inputs_desc[i]['required']:
              # missing file
              raise cherrypy.HTTPError(400, # Bad Request
                                       "Missing input file number {0}".format(i))
            else:
                # skip this input
                continue

          # suppose than the file is in the correct format for its extension
          ext = inputs_desc[i]['ext']
          file_save = file(os.path.join(work_dir,'input_%i' % i + ext), 'wb')

          size = 0
          while True:
            # TODO larger data size
            data = file_up.file.read(128)
            if not data:
                break
            size += len(data)
            if 'max_weight' in inputs_desc[i] and size > eval(str(inputs_desc[i]['max_weight'])):
                # file too heavy
                raise cherrypy.HTTPError(400, # Bad Request
                                          "File too large, " +
                                          "resize or use better compression")
            file_save.write(data)
          file_save.close()
        #msg = self.process_inputs()
        #self.log("input uploaded")
        #self.cfg['meta']['original'] = True
        #self.cfg['meta']['max_width']  = self.max_width;
        #self.cfg['meta']['max_height'] = self.max_height;
        #self.cfg.save()

        return 



    #---------------------------------------------------------------------------
    def crop_input(self, idx, demo_id, key, inputs_desc, crop_info):
        """
        Crop input if selected
            idx: input position
            demo_id
            key
            inputs_desc
            crop_info
        """

        print "#### crop_input ####"
        start = timer()
        res_data = {}
        res_data['info'] = ""
        # for the moment, we can only crop the first image
        if idx!=0:
            res_data[status] = "KO"
            return res_data
            
        work_dir = self.WorkDir(demo_id,key)
        initial_filename = os.path.join(work_dir,'input_{0}.orig.png'.format(idx))
        cropped_filename = os.path.join(work_dir,'input_{0}.crop.png'.format(idx))
        res_data['filename'] = cropped_filename
        print "crop_info = ",crop_info
        
        if crop_info["enabled"]:
            # define x0,y0,x1,y1
            x0 = int(round(crop_info['x']))
            y0 = int(round(crop_info['y']))
            x1 = int(round(crop_info['x']+crop_info['w']))
            y1 = int(round(crop_info['y']+crop_info['h']))
            #save parameters
            try:
                #
                # cut subimage from original image
                #
                # draw selected rectangle on the image
                imgS        = image(initial_filename)
                # TODO: get rid of eval()
                max_pixels  = eval(str(inputs_desc[0]['max_pixels']))
                imgS.draw_line([(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)],
                                color="red")
                imgS.draw_line([(x0+1, y0+1), (x1-1, y0+1), (x1-1, y1-1),
                                (x0+1, y1-1), (x0+1, y0+1)], color="white")
                imgS.save(os.path.join(work_dir,'input_{0}s.png'.format(idx)))
                
                # Karl: here different from base_app approach
                # crop coordinates are on original image size
                img = image(initial_filename)
                img.crop((x0, y0, x1, y1))
                # resize if cropped image is too big
                if max_pixels and prod(img.size) > max_pixels:
                    img.resize(max_pixels, method="antialias")
                # save result
                img.save(cropped_filename)

            except ValueError:
                res_data["status"] = "KO"
                res_data['info'] += " cropping failed with exception;"
                # TODO deal with errors in a clean way
                raise cherrypy.HTTPError(400, # Bad Request
                                            "Incorrect parameters, " +
                                            "image cropping failed.")
        else:
            res_data["status"]  = "KO"
            res_data['info'] += " no cropping area selected;"
            return res_data

        res_data["status"]  = "OK"
        end=timer()
        res_data["info"]    += " crop_input took: {0} seconds;".format(end-start)
        return res_data


    #---------------------------------------------------------------------------
    @cherrypy.expose
    def input_select_and_crop(self, **kwargs):
        """
        use the selected available input images
        input parameters:
            demo_id
            ddl_inputs
            url
            list of inputs
        returns:
            { key, status, message }
        """
        print "#### input_select ####"
        res_data = {}
        res_data['info'] = ''
        # we need a unique key for the execution
        demo_id = kwargs.pop('demo_id',None)
        key = self.get_new_key(demo_id)
        res_data["key"]     = key
        work_dir = self.WorkDir(demo_id,key)
        inputs_desc = kwargs.pop('ddl_inputs',None)
        inputs_desc = json.loads(inputs_desc)

        crop_info   = kwargs.pop('crop_info',None)
        crop_info   = json.loads(crop_info)

        nb_inputs = len(inputs_desc)

        blob_url = kwargs.pop('url',None)
        print "blob_url", blob_url
        print "kwargs",kwargs
        
        print "\n-----\ninput_select :", kwargs.keys()
        # copy to work_dir
        blobfile = urllib.URLopener()
        for inputinfo in kwargs.keys():
          print "\n**\n"
          # 1. retreive index
          posstart=inputinfo.index(':')
          idx = int(inputinfo[:posstart])
          #print inputs_desc[idx]
          inputinfo = inputinfo[posstart+1:]
          if ',' in inputinfo:
            # what should we do ? we should have two files here...
            inputfiles = inputinfo.split(',')
          else:
            inputfiles = [ inputinfo ]
          # extract input files to work dir as input_%i.ext
          print "inputfiles:",inputfiles
          for inputfile in inputfiles:
            print "---- inputfile: '{0}'".format(inputfile)
            print type(inputfile)
            basename  = inputfile[:inputfile.index('.')]
            ext       = inputfile[inputfile.index('.'):]
            print "basename :", basename
            blob_link =  blob_url +'/'+ basename + ext
            print "blob_link = ", blob_link
            blobfile.retrieve(blob_link, 
                              os.path.join(work_dir,'input_{0}{1}'.format(idx,ext)))
        
        msg = self.process_inputs(demo_id, key, inputs_desc,crop_info, res_data)
        ##self2.log("input selected : %s" % kwargs.keys()[0])
        #self.cfg['meta']['original'] = False
        #self.cfg['meta']['max_width']  = self.max_width;
        #self.cfg['meta']['max_height'] = self.max_height;
        #self.cfg.save()

        # Let users copy non-standard input into the work dir
        # don't have fnames here
        #self2.input_select_callback(fnames)

        ## jump to the params page
        #return self.params(msg=msg, key=self2.key)
        
        res_data["status"]  = "OK"
        res_data["message"] = "input files copied to the local path"
        return json.dumps(res_data)


    #---------------------------------------------------------------------------
    @cherrypy.expose
    def run_demo(self, demo_id, key, ddl_run, params):
        
        res_data = {}
        res_data["key"] = key
        print "#### run demo ####"
        print "demo_id = ",demo_id
        print "key = ",key
        ddl_run = json.loads(ddl_run)
        print "ddl_run = ",ddl_run
        params  = json.loads(params)
        print "params = ",params
        res_data["work_url"] = self.WorkUrl(demo_id,key)
        res_data['params']   = params
        
        # run the algorithm
        try:
            run_time = time.time()
            #self.cfg.save()
            self.run_algo(demo_id,key,ddl_run, params)
            #self.cfg.Reload()
            ## re-read the config in case it changed during the execution
            res_data['run_time'] = time.time()-run_time
            res_data['status'] = 'OK'
        except IPOLTimeoutError:
            res_data['status'] = 'KO'
            res_data['error'] = 'timeout'
        except RuntimeError as e:
            #print "self.show_results_on_error =", self.show_results_on_error
            #if not(self.show_results_on_error):
                #return self.error(errcode='runtime',errmsg=str(e))
            #else:
                #self.cfg['info']['run_time'] = time.time() - run_time
                #self.cfg['info']['status']   = 'failure'
                #self.cfg['info']['error']    = str(e)
                #self.cfg.save()
                #pass
            res_data['run_time'] = time.time() - run_time
            res_data['status']   = 'KO'
            res_data['error']    = str(e)
        return json.dumps(res_data)
        
        
    #---------------------------------------------------------------------------
    # Core algorithm runner
    #---------------------------------------------------------------------------
    def run_algo(self,demo_id,key,ddl_run,params):
        """
        the core algo runner
        """
        
        # refresh demo description ??
      
        work_dir = self.WorkDir(demo_id,key)
        base_dir = self.BaseDir(demo_id,key)
        rd = run_demo_base.RunDemoBase(base_dir, work_dir)
        rd.set_logger(cherrypy.log)
        #if 'demo.extra_path' in cherrypy.config:
            #rd.set_extra_path(cherrypy.config['demo.extra_path'])
        rd.set_algo_params(params)
        rd.set_algo_info  ({})
        rd.set_algo_meta  ({})
        #rd.set_algo_info  (self.cfg['info'])
        #rd.set_algo_meta  (self.cfg['meta'])
        #rd.set_MATLAB_path(self.get_MATLAB_path())
        rd.set_demo_id(demo_id)
        rd.set_commands(ddl_run)
        rd.run_algo()
        ## take into account possible changes in parameters
        #self.cfg['param'] = rd.get_algo_params()
        #self.cfg['info']  = rd.get_algo_info()
        #self.cfg['meta']  = rd.get_algo_meta()
        #print "self.cgf['param']=",self.cfg['param']
        return
