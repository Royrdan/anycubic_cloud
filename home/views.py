import sys
import os.path
import os
from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseBadRequest
from django.views import View
from .forms import upload_form
from django.conf import settings

sys.path.insert(0, os.getcwd())
import anycubic_cloud_module


# Create your views here.
global cloud
cloud = None


def return_home(request, message=""):
    global cloud
    if cloud:
        if cloud.logged_in:
            cloud.get_jobs()
            cloud.get_printers()
            cloud.get_gcodes()
            content = {
                'name': cloud.nickname,
                'jobs': cloud.jobs,
                'printers': cloud.printers,
                'current_jobs': cloud.current_jobs,
                'upload_form': upload_form,
                'message': message,
            }
            return render(request, 'home/home.html', content)
    return redirect('login_view')


class home_view(View):
    def get(self, request):
        return return_home(request)


class printer_list(View):
    def get(self, request):
        global cloud
        if cloud:
            content = {
                'printers': cloud.get_printers(),
            }
            return render(request, 'home/printer_list.html', content)
        else:
            return redirect('login_view')


class gcode_list(View):
    def get(self, request):
        global cloud
        if cloud:
            cloud.get_gcodes()
            content = {
                'gcodes': cloud.gcodes
            }
            return render(request, 'home/gcode_list.html', content)
        else:
            return redirect('login_view')


class job_list(View):
    def get(self, request):
        global cloud
        if cloud:
            cloud.get_jobs()
            content = {
                'jobs': cloud.jobs
            }
            return render(request, 'home/job_list.html', content)
        else:
            return redirect('login_view')


class current_job_list(View):
    def get(self, request):
        global cloud
        if cloud:
            content = {
                'current_jobs': cloud.get_current_jobs()
            }
            return render(request, 'home/taskbar_job_progress.html', content)
        else:
            return redirect('login_view')


class current_job_detail_list(View):
    def get(self, request):
        global cloud
        if cloud:
            content = {
                'current_jobs_detail': cloud.get_current_jobs()
            }
            return render(request, 'home/current_job_list.html', content)
        else:
            return redirect('login_view')


class login_view(View):
    def get(self, request):
        global cloud
        if not cloud:
            return render(request, 'home/login.html', {})
        else:
            if cloud.logged_in:
                return redirect('home_view')
            else:
                return render(request, 'home/login.html', {})

    def post(self, request):
        global cloud
        email = request.POST.get('email')
        password = request.POST.get('password')
        content = None
        if len(email) == 0:
            content = {'error': 'Email cannot be blank'}
        elif '@' not in email:
            content = {'error': 'Please enter a valid email'}
        elif len(password) == 0:
            content = {'error': 'Password cannot be blank'}
        if content:
            # Return with an error
            return render(request, 'home/login.html', content)
        else:
            if cloud:
                if cloud.logged_in:
                    return redirect('home_view')
                else:
                    cloud.username = email
                    cloud.password = password
            else:
                cloud = anycubic_cloud_module.anycubic_cloud_session(email, password)

            login_success, login_message = cloud.login()
            if login_success:
                return redirect('home_view')
            else:
                content = {'error': login_message}
                return render(request, 'home/login.html', content)


class printer_view(View):

    def get(self, request, id):
        global cloud
        if cloud:
            if not cloud.logged_in:
                return redirect('login_view')
        else:
            return redirect('login_view')

        cloud.get_printers()
        # Search for the ID
        printer = None
        for p in cloud.printers:
            if id == p.id:
                printer = p
                break
        if not p:
            print("Error: Unable to find the printer ID")
            return redirect('home_view')

        content = {
            'printer': printer
        }
        return render(request, 'home/printer.html', content)


class gcode_view(View):

    def get(self, request, id):
        global cloud
        if cloud:
            if not cloud.logged_in:
                return redirect('login_view')
        else:
            return redirect('login_view')

        #cloud.get_gcodes()
        # Search for the ID
        gcode = None
        for g in cloud.gcodes:
            if id == g.id:
                gcode = g
                break
        if not g:
            print("Error: Unable to find the gcode ID")
            return redirect('home_view')

        content = {
            'gcode': gcode
        }
        return render(request, 'home/gcode.html', content)

    def post(self, request, id):
        global cloud
        if cloud:
            if not cloud.logged_in:
                return redirect('login_view')
        else:
            return redirect('login_view')

        action = request.POST.get('action')
        if action is None:
            return return_home(request, 'Error: Received invalid post data.<br> Please try again.')

        gcode = None
        for g in cloud.gcodes:
            if id == g.id:
                gcode = g
                break
        if not g:
            print("Error: Unable to find the gcode ID")
            return return_home(request, 'Error: Unable to find the gcode ID')

        # DELETE GCODE
        if action == 'delete':
            delete, message = cloud.delete( gcode_id=int(id) )
            return HttpResponse(message)

        # PRINT GCODE
        elif action == 'print':
            printer_id = request.POST.get('printer_id')
            if (printer_id):
                p, message = cloud.print(gcode.id, printer_id=printer_id)

                return HttpResponse(message) # Success or failure return message
            else:
                return return_home(request, "Couldnt find printer ID")

        else:
            return return_home(request, 'Invalid action for gcode file')


class upload_view(View):

    def get(self, request):
        global cloud
        if cloud:
            if not cloud.logged_in:
                return redirect('login_view')
            else:
                return redirect('home_view')
        else:
            return redirect('login_view')

    def post(self, request):
        global cloud
        if cloud:
            if not cloud.logged_in:
                return redirect('login_view')
        else:
            return redirect('login_view')

        file_data = upload_form(request.POST, request.FILES)
        if file_data.is_valid():
            uploaded_file = file_data.save()
        else:
            return return_home(request, 'Invalid data received when uploading file')

        filename = str(settings.MEDIA_ROOT / "uploads" / uploaded_file.full_path())

        upload, upload_message = cloud.upload(filename)
        uploaded_file.delete()
        os.remove(filename) # Remove the file. Maybe add some error checking here
        if not upload:
            print(upload_message)
            return return_home(request, upload_message)

        return return_home(request, 'Uploaded Successfully')


class logout_view(View):
    def get(self, request):
        global cloud
        if cloud:
            cloud = None
        return redirect('login_view')


class test(View):
    def post(self, request):
        global cloud
        if cloud:
            if not cloud.logged_in:
                return redirect('login_view')
        else:
            return redirect('login_view')
        # Only used for testing purposes
        try:
            category = request.POST.get('category')
            command = request.POST.get('command')
            data_raw = request.POST.get('data')
        except Exception as e:
            print(f"TEST ERROR - {e}")
            return redirect('home_view')
        else:
            variables = {}
            if data_raw != "":
                try:
                    data_raw = data_raw.split(' ')
                    for v in data_raw:
                        v_name = v.split('=')[0]
                        v_value = v.split('=')[1]
                        try:
                            v_value = int(v_value)
                        except:
                            pass
                        variables[v_name] = v_value
                except Exception as e:
                    return HttpResponse(e)

            test, message = cloud.command( category, command, **variables)
            if test:
                return HttpResponse(str(test))
            else:
                return HttpResponse(message)
