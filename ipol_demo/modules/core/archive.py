#!/usr/bin/env python3
# -*- coding:utf-8 -*-

"""
Helper functions for core, related to the archive module.
"""

import gzip
import json
import os
import traceback
from collections import OrderedDict

import requests
from ipolutils.utils import thumbnail


def create_thumbnail(src_file):
    """
    Create thumbnail when possible from file to archive in run folder,
    returns the filepath of thumbnail when created.
    """
    thumb_height = 128
    if not os.path.exists(src_file):
        return False
    thumb_name = os.path.basename(src_file).replace(".", "_")
    thumb_name = thumb_name.lower() + '_thumbnail.jpeg'
    thumb_file = os.path.join(os.path.dirname(src_file), thumb_name)
    try:
        thumbnail(src_file, thumb_height, thumb_file)
    except Exception:
        return False
    return thumb_file

def send_to_archive(demo_id, work_dir, request, ddl_archive, res_data, host_name):
    """
    Prepare an execution folder for archiving an experiment (thumbnails).
    Collect information and parameters.
    Send data to the archive module.
    """
    # let's add all the parameters
    parameters = OrderedDict()
    blobs = []
    for key, values in ddl_archive.items():
        if  key == 'params':
            for p in values:
                if p in res_data['params']:
                    parameters[p] = res_data['params'][p]
        elif key == 'info':
            for i in values:
                if i in res_data['algo_info']:
                    parameters[values[i]] = res_data['algo_info'][i]
        elif key in ('files', 'hidden_files'):
            for file_name, file_label in values.items():

                src_file = os.path.join(work_dir, file_name)
                if not os.path.exists(src_file):
                    continue # declared file in ddl is not there

                if not file_label: # if no label given, use filename
                    file_label = file_name
                value = {file_label: src_file}
                try: # to get a thumbnail
                    print(src_file)
                    thumb_file = create_thumbnail(src_file)
                except Exception:
                    print(traceback.format_exc())
                if thumb_file:
                    value[os.path.basename(thumb_file)] = thumb_file
                blobs.append(value)
        elif  key == 'compressed_files':
            for file_name, file_label in values.items():

                src_file = os.path.join(work_dir, file_name)
                if not os.path.exists(src_file):
                    continue # normal?

                src_handle = open(src_file, 'rb')
                gz_file = src_file + '.gz'
                gz_handle = gzip.open(gz_file, 'wb')
                gz_handle.writelines(src_handle)
                src_handle.close()
                gz_handle.close()

                if not file_label: # if no label given, use filename
                    file_label = file_name
                blobs.append({file_label: gz_file})

    if 'enable_reconstruct' in ddl_archive and ddl_archive['enable_reconstruct'] and request is not None:
        clientData = json.loads(request['clientData'])

        if clientData.get("origin", "") == "upload":
            # Count how many file entries and remove them
            file_keys = [key for key in request if key.startswith("file_")]
            files = request.copy()
            list(map(files.pop, file_keys))
            clientData["files"] = len(file_keys)

        execution = {}
        execution['demo_id'] = demo_id
        execution['request'] = clientData
        execution['response'] = res_data

        execution_json = json.dumps(execution)
    else:
        execution_json = None

    url = 'http://{}/api/archive/add_experiment'.format(host_name)
    data = {
        "demo_id": demo_id,
        "blobs": json.dumps(blobs),
        "parameters": json.dumps(parameters),
        "execution": execution_json
    }
    resp = requests.post(url, data=data)
    return resp.json()
