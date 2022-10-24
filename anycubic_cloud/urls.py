"""anycubic_cloud URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from home import views as home_views

urlpatterns = [
    path('', home_views.home_view.as_view(), name='home_view'),
    path('login/', home_views.login_view.as_view(), name='login_view'),
    path('printers/', home_views.printer_list.as_view(), name='printer_list'),
    path('gcodes/', home_views.gcode_list.as_view(), name='gcode_list'),
    path('jobs/', home_views.job_list.as_view(), name='job_list'),
    path('current-jobs/', home_views.current_job_list.as_view(), name='current_job_list'),
    path('current-jobs_detail/', home_views.current_job_detail_list.as_view(), name='current_job_detail_list'),
    path('printer/<int:id>', home_views.printer_view.as_view(), name='printer_view'),
    path('gcode/<int:id>', home_views.gcode_view.as_view(), name='gcode_view'),
    path('upload/', home_views.upload_view.as_view(), name='upload_view'),
    path('logout/', home_views.logout_view.as_view(), name='logout_view'),
    path('test/', home_views.test.as_view(), name='test'),
    path('admin/', admin.site.urls),
]
