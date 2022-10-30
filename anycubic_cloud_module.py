import os
import requests as req
import sys
from urllib.parse import unquote as url_decode
from urllib.parse import urlencode
import hashlib
import yaml
from desktop_notifier import DesktopNotifier
from datetime import datetime
import json


def md5(filename):
    with open(filename, "rb") as f:
        bytes = f.read()
        return hashlib.md5(bytes).hexdigest()


def get_password(secrets_file):
    try:
        with open(secrets_file) as s:
            secrets = yaml.load(s, Loader=yaml.FullLoader)
            return secrets['anycubic_cloud']
    except:
        print("Failed to open secrets file " + secrets)
        sys.exit()


def get_api(filename):
    try:
        with open(filename) as a:
            api = yaml.load(a, Loader=yaml.FullLoader)
            return api
    except Exception as e:
        print(f"Failed to load API file from {filename}. {e}")
        sys.exit()


def timestamp_to_string(t, reverse=False):
    last_update = datetime.now() - datetime.fromtimestamp( t )
    if reverse: last_update = -1 * last_update
    last_update = round(last_update.total_seconds() / 60)
    return f'{last_update} mins ago'

def seconds_to_string(t):
    return t


class printer():

    def __init__(self, **kwargs):
        try:
            self.__dict__.update(kwargs)

            # Set Printing Status
            if self.is_printing == 1:
                self.is_printing = 'No'
            elif self.is_printing == 2:
                self.is_printing = 'Yes'

            self.create_time = timestamp_to_string(self.create_time)
            self.last_update_time = timestamp_to_string(self.last_update_time)
        except:
            return None


class gcode():

    def __init__(self, **kwargs):
        try:
            self.__dict__.update(kwargs)
            self.name = self.name.replace('.pwmb', '')
            self.create_time = timestamp_to_string(self.create_time)
            self.estimate = round(self.estimate / 60, 0)
            self.supplies_usage = round(self.supplies_usage, 2)
            # Put price per litre in here
            self.price = round((35 / 1000) * self.supplies_usage, 2)
            self.z_thick = round(self.z_thick, 0)
        except:
            return None


class job():

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

        # Status
        if self.print_status == 1:
            self.print_status = 'Printing'
        elif self.print_status == 2:
            self.print_status = 'Complete'

        # Paused
        if self.pause == 0:
            self.pause = 'No'
        elif self.pause == 1:
            self.pause = 'Yes'
        elif self.pause == 2:
            self.pause = 'Canceled'

        self.gcode_name = self.gcode_name.replace('.pwmb', '')
        self.estimate = self.estimate / 60
        self.last_update_time = timestamp_to_string(self.last_update_time)
        self.material = round(float(self.material), 2)
        self.create_time = timestamp_to_string(self.create_time)
        self.start_time = timestamp_to_string(self.start_time)
        self.end_time = timestamp_to_string(self.end_time)



class anycubic_cloud_session():

    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.logged_in = False
        self.token = None
        self.user_id = None
        self.space_used = None
        self.printers = []
        self.gcodes = []
        self.jobs = []
        self.current_jobs = []
        self.printers_last_updated = None
        self.gcodes_last_updated = None
        self.jobs_last_updated = None
        self.current_jobs_last_updated = None

        self.base_url = "https://api.cloud.anycubic.com/"
        local_path = os.path.dirname(__file__)

        self.api = get_api( os.path.join(local_path, "api_endpoints.yaml") )
        self.error_file = os.path.join(local_path, "errors.txt")
        self.notifier = DesktopNotifier()

    def command(self, category, command, params=None, postfix="", **kwargs):

        if category not in self.api:
            self.log_error(f'Error: Category {category} doesnt exist')
            return None, f'Error: Category {category} doesnt exist'
        if command not in self.api[category]:
            self.log_error(f'Error: Command {command} doesnt exist')
            return None, f'Error: Command {command} doesnt exist'
        data = self.api[category][command]
        if 'method' not in data:
            self.log_error('Error: No method defined in the api file for command: {command}.')
            return None, 'Error: No method defined in the api file for command: {command}.'
        if data['method'] not in ['POST', 'GET', 'DELETE']:
            self.log_error(f'Error: Method: {data["method"]} is not valid for command: {command}.')
            return None, f'Error: Method: {data["method"]} is not valid for command: {command}.'
        if 'endpoint' not in data:
            self.log_error('Error: No endpoint defined in the api file for command: {command}.')
            return None, 'Error: No endpoint defined in the api file for command: {command}.'

        method = data['method']
        endpoint = data['endpoint']
        if 'variables' in data:
            variables = data['variables'].split(' ')
        else:
            variables = None

        data = {}
        if variables:
            for v in variables:
                if v == "username":
                    data[v] = self.username
                elif v == "password":
                    data[v] = self.password
                elif v == "device_type":
                    data[v] = 'pc'
                elif v == "login_type":
                    data[v] = 1
                elif v == "user_id":
                    if self.user_id is None:
                        self.login()
                        data[v] = self.user_id
                elif v == "email":
                    data[v] = self.username
                else:
                    try:
                        data[v] = vars()['kwargs'][v]
                    except Exception as e:
                        self.log_error(f"Variable \'{v}\' does not exist but is required for {command}")
                        return None, f"Variable \'{v}\' does not exist but is required for {command}"
                    else:
                        if '{id}' in endpoint:
                            endpoint = endpoint.replace('{id}', str(data[v]))

        headers = {}
        if command != 'login':
            if not self.logged_in:
                self.login()
            headers = {
                "XX-Device-Type": "pc",
                "XX-Token": self.token,
            }

        params_str = ""
        if params:
            params_str = urlencode(params)

        url = f"{self.base_url}{endpoint}{params_str}/{postfix}"

        print(f'    Command: {category} - {command} - {method} url: {url}')
        if command != 'login':
            print(f'    data: {data}')
        else:
            print(f'    data: **HIDDEN**')
        if method == "POST":
            r = req.post(url, headers=headers, data=data)
        elif method == "DELETE":
            r = req.delete(url, headers=headers, data=data)
        else:
            r = req.get(url, headers=headers, data=data)

        if r.status_code == 200:
            if r.json()['code'] == 1:
                return r.json(), r.json()['msg']
            elif r.json()['code'] == 10001: # Login expired
                self.log_error(f'Login Expired. Relogging in {r.text}')
                self.login()
                return self.command(category, command, params, postfix, **kwargs)
            else:
                print(r.text)
                self.log_error(r.json()['msg'])
                return None, r.json()['msg']
        else:
            self.log_error(f'Request threw error with code {r.status_code}')
            return None, f'Request threw error with code {r.status_code}'

    def log_error(self, error):
        print(error)
        self.notifier.send_sync('Anycubic Cloud', error)
        #with open(self.error_file, 'a+') as myfile:
        #    myfile.write(error)

    def login(self):
        r, message = self.command('user', 'login')
        if r:
            try:
                login_data = r
                self.token = login_data['data']['token']
                self.user_id = login_data['data']['user']['id']
                self.nickname = login_data['data']['user']['user_nickname']
                self.space_used = login_data['data']['user']['uploadsize_status']['used'] + "/" + login_data['data']['user']['uploadsize_status']['total']
            except:
                try:
                    error_msg = r['msg']
                except:
                    error_msg = "Unknown error"
                self.log_error(f'Received invalid data from login: {error_msg}')
                return False, error_msg
            else:
                self.logged_in = True
                return True, "Success"

        else:
            self.log_error(message)
            return None, message

    def upload(self, file):
        if not os.path.exists(file):
            self.log_error(f"File {file} cannot be found. Please check your path and try again.")
            return None, f"Filename {file} does not exist"
        filename = file.split('/')[-1]
        params = {
            'filename': filename,
            'md5': md5(file),
        }
        upload_data, message = self.command('gcode', 'upload', params=params)
        if upload_data:
            try:
                upload_url = upload_data['data']['url']
            except Exception as e:
                self.log_error(f'Received invalid data for the upload url: {e}')
                return None, f'Received invalid data for the upload url: {e}'
            else:
                print(f"uploading to url: {upload_url}")
                upload = req.put(upload_url, data=open(file, 'rb'))
                if upload.status_code != 200:
                    log_error(f'Anycubic upload file failed with status code: {upload_data.status_code}')
                else:
                    self.notifier.send_sync('File upload was successful', f'{filename} was successfully uploaded')
                    print("Upload successful")
                return upload, "Success"
        else:
            return None, message

    def delete(self, gcode_id):
        # apparently needs to be a string
        delete, message = self.command('gcode', 'delete', id=str(gcode_id))
        print(delete)
        print(message)
        if delete:
            return delete, message
        else:
            return None, message

    def get_printers(self):
        if self.printers_last_updated is not None:
            if (datetime.now() - self.printers_last_updated).total_seconds() < 30:
                return self.printers
        data_raw, message = self.command('printer', 'get', page=1)
        if data_raw:
            try:
                data = data_raw['data']
                self.printers = []
                for p in data:
                    self.printers.append(
                        printer(**p)
                    )
                self.printers_last_updated = datetime.now()

                return self.printers
            except Exception as e:
                self.log_error(f'Invalid Data received when retrieving printers. {e}')
                return []
        else:
            self.log_error(message)
            return []

    def get_gcodes(self):
        if self.gcodes_last_updated is not None:
            if (datetime.now() - self.gcodes_last_updated).total_seconds() < 30:
                return "Success", "Success"
        data_raw, message = self.command('gcode', 'get_gcodes', page=1)
        if data_raw:
            try:
                data = data_raw['data']
                self.gcodes = []
                for g in data:
                    # Move Slice Param into the main dictionary
                    slice_param = json.loads(g['slice_param'])
                    for item in slice_param:
                        if item != 'advanced_control':
                            g[item] = slice_param[item]
                    del g['slice_param']
                    del g['slice_result']
                    self.gcodes.append(gcode(**g))
                self.gcodes_last_updated = datetime.now()
                return "Success", "Success"
            except Exception as e:
                self.log_error(f'Invalid Data received when retrieving gcode files. {e}')
                return None, f'Invalid Data received when retrieving gcode files. {e}'
        else:
            self.log_error(message)
            return None, message

    def get_jobs(self):
        print(self.jobs_last_updated)
        if self.jobs_last_updated != None:
            if (datetime.now() - self.jobs_last_updated).total_seconds() < 30:
                return "Success", "Success"
        data_raw, message = self.command('jobs', 'get_jobs', page=0, print_status=0, gcode_id=0)
        if data_raw:
            try:
                data = data_raw['data']
                self.jobs = []
                for j in data:
                    self.jobs.append(job(**j))
                self.jobs_last_updated = datetime.now()
                return "Success", "Success"
            except Exception as e:
                self.log_error(f'Invalid Data received when retrieving job files. {e}')
                return None, f'Invalid Data received when retrieving jop files. {e}'
        else:
            self.log_error(message)
            return None, message

    def get_current_jobs(self):
        if self.current_jobs_last_updated is not None:
            if (datetime.now() - self.current_jobs_last_updated).total_seconds() < 30:
                return self.current_jobs
        self.get_jobs()
        self.current_jobs = []
        for job in self.jobs:
            if job.progress != 100 and job.print_status == 'Printing':
                self.current_jobs.append(job)
        return self.current_jobs

    def slice(self, file, slice_params):
        ## Maybe has an inbuild slicer that works with this?
        s, message = self.command(
            'gcode',
            'send_gcode',
            filename=str(file.split('/')[-1]), # Remove the user ID
            slice_param=slice_params,
            matrix='',
            mirror='0,0,0',
            slice_support=None
        )

        if s:
            return s, "Success"
        else:
            return None, message

    def print(self, gcode_id, printer_id):
        p, message = self.command(
            'gcode',
            'print',
            gcode_id=gcode_id,
            printer_id=printer_id,
            project_id=0,
            order_id=1,
            type="",
            settings=None
        )
        """
        settings = {
            bottom_layers;
            bottom_time;
            off_time;
            on_time;
            z_down_speed;
            z_up_height;
            z_up_speed;
        }
        """

        if p:
            print(p)
            return "Print started successfully", message
        elif message == 'failed to send print file': # OR SOMETHING ALONG THESE LINES???
            print(p)
            return "Success", "Success"
        else:
            print(p) # Get the error message from here as its actually successful
            return None, message

    def get_video(self, printer_id):
        return None
