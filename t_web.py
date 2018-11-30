#!/usr/bin/python3

# Import Libraries
import os, os.path
import cherrypy
import random
import csv
import json
import sys
import time
from pprint import pprint
import stat
import collections
import re
import datetime
import subprocess

import traceback

import solo
solo.chk_and_stopall(__file__)

import argparse
parser = argparse.ArgumentParser()
parser.add_argument("-q", help="Run in embedded mode",action="store_true")
args = parser.parse_args()

# ------- GPIO stuff -----------
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)
# ------------------------------

# -------  Auth   -------
# Doesn't work on chrome
#from cherrypy.lib import auth_digest
#Users = {'root': 'root'}
# --------------------------
# Try this instead...
from webauth import AuthSession

# Common file specifications
import fspec

# Load local packages
sys.path.insert(0,'./packages/')
from templaterex import TemplateRex

class PyServ(object):

   def __init__(self):

      self.version = 1.0;

      # Create deque for tail
      self.tail_max = 20
      self.tail = collections.deque(maxlen=self.tail_max)

      # Test stuff... erase later.
      self.cnt = 1
      self.inc=0

      self.pwr_btn = [ {'pin':38, 'lbl':'Alpha'}, {'pin':40, 'lbl':'Beta'} ]

      for btn_hsh in self.pwr_btn:
         GPIO.setup( btn_hsh['pin'], GPIO.OUT)

      self.auth = AuthSession(url_login="/webpanel/auth/login")

   # ------------------------
   @cherrypy.expose
   def index(self):

      data_hsh = {}
      root_path = os.getcwd()

      trex = TemplateRex(fname='t_mon_index.html')

      self._header(trex)

      # Last Measurement
      rtn_json = self._read_json(fspec.t_last)
      if rtn_json:

         # json is returned as a list of hash
         for dev_hsh in rtn_json['json']:
            trex.render_sec('t_row',dev_hsh)

         diff_time = time.time() - rtn_json['stat'].st_mtime

         if diff_time > 20:
            trex.render_sec('stale_warn',{'diff_time':str(diff_time)})

      else:
         trex.render_sec('no_last',{})

      # Display power down events.
      if os.path.isfile(fspec.pwr_down_log):
         cmd_lst = ['tail','-3',fspec.pwr_down_log]
         rtn = subprocess.run(cmd_lst, stdout=subprocess.PIPE)
         log_tail = rtn.stdout.decode('utf-8')

         log_lst = log_tail.splitlines()
         log_lst.reverse()

         for log_line in log_lst:
            trex.render_sec('log_row',{'log_line':log_line})
      else:
            uptime_str = self._uptime()
            trex.render_sec('no_events',{'uptime_str':uptime_str})

      data_hsh['version'] = self.version

      try:
         fd = open(fspec.state_json,'r')
         data_hsh["plot_data"]= fd.read()
         fd.close()
      except:
         data_hsh['err_msg'] = "Cannot open State file..."

      trex.render_sec('content',data_hsh)

      page = trex.render({'refresh':7})

      return page

   # ------------------------
   @cherrypy.expose
   def control_disp(self, **params):

      data_hsh = {}

      data_hsh['username'] = self.auth.authorize()

      trex = TemplateRex(fname='t_mon_control_disp.html')

      # ---- Control this is where it happens -------

      if 'pwr_selected' in params:
         pin = self.pwr_btn[int(params['pwr_selected'])]['pin']
         GPIO.output(pin,int(params['on_off']))
      # ---------------------------------------------

      self._header(trex)

      for inx,btn_hsh in enumerate(self.pwr_btn):

         btn_hsh['inx'] = inx
         if GPIO.input(btn_hsh['pin']):
            btn_hsh['checked'] = 'checked'
            trex.render_sec('sldr_set',btn_hsh)

         else:
            btn_hsh['checked'] = ''
            trex.render_sec('sldr_set',btn_hsh)

      return( self.render_layout(trex,locals()) )

   # ------------------------
   @cherrypy.expose
   def control_ctl(self, **vars):

      ##pprint(cherrypy.request.params)
      pprint(vars)

      raise cherrypy.HTTPRedirect('/control_disp')

   # --------------------------------------------
   # utility functions
   # --------------------------------------------

   # --------------------------------------------
   # Common featured called at the end of each callback abstracted out
   def render_layout(self,trex,data_hsh={}):

      data_hsh['version'] = self.version
      trex.render_sec('content',data_hsh)

      if cherrypy.request.login:
         trex.render_sec('logged_in',{'user':cherrypy.request.login})

      return(trex.render(data_hsh))

   # -----------------------
   def _header(self,trex):

      # Display current status on all pages
      for btn_hsh in self.pwr_btn:
         pprint(btn_hsh['lbl'])
         if GPIO.input(btn_hsh['pin']):
            trex.render_sec('stat_on',btn_hsh)
         else:
            trex.render_sec('stat_off',btn_hsh)

         trex.render_sec('stat_grp')


   # -----------------------
   def _uptime(self):
      with open('/proc/uptime', 'r') as fid:
         uptime_seconds = float(fid.readline().split()[0])
         uptime_str = str(datetime.timedelta(seconds = uptime_seconds))
         uptime_str = re.sub('\.\d+$','',uptime_str)
      return(uptime_str)

   def _read_json(self,fspec,try_max=20):
      try_inx = 1
      if os.path.isfile(fspec):
         while try_inx < try_max:
            try:
               fd = open(fspec,'r')
               rtn = {}
               rtn['json'] = json.loads(fd.read())
               rtn['stat'] = os.stat(fspec)
               fd.close()
               return(rtn)
            except:
               try_inx = try_inx + 1
               print("Unexpected error:", sys.exc_info()[0])
               print(traceback.format_exc())
      print(">>> {}".format(try_inx))
      return(False)



####### End of Class PyServ #############
port = 9090

if __name__ == '__main__':

   #dir_session = './sessions'
   #if not os.path.exists(dir_session):
   #       print "making dir",dir_session
   #       os.mkdir(dir_session)
   #import inspect
   #print(inspect.getfile(TemplateRex))

   if not args.q:
      print("\nStarting {} Server\n".format(__file__))
      print("Use Chrome and go to port {}/\n".format(port))

   dir_session = '/tmp/sessions'
   if not os.path.exists(dir_session):
          os.mkdir(dir_session)

   cherrypy.config.update({'tools.sessions.storage_type':"file"})
   cherrypy.config.update({'tools.sessions.storage_path':dir_session})

   cherrypy.config.update({'tools.sessions.on': True})
   cherrypy.config.update({'tools.sessions.timeout': 99999})

   cherrypy.config.update({'server.socket_port': port})
   cherrypy.config.update({'server.socket_host': "0.0.0.0" })

   # ------- doesn't work on chrome -----
   #digest_conf = {'tools.auth_digest.on': True,
   #'tools.auth_digest.realm': 'power',
   #'tools.auth_digest.get_ha1': auth_digest.get_ha1_dict_plain(Users),
   #'tools.auth_digest.key': '1245678900987654321'
   #}
   #cherrypy.config.update(digest_conf)
   # --------------

   # ---- SSL cert ---- <--- doesn't work and no fix is offered
   #cherrypy.config.update({'server.ssl_module': 'builtin' })
   #cherrypy.config.update({'server.ssl_certificate': './conf/cert.pem' })
   #cherrypy.config.update({'server.ssl_private_key': './conf/privkey.pem' })
   # --------------

   # Run in embedded mode
   if args.q:
      cherrypy.config.update({'environment': 'production'})
      cherrypy.config.update({'log.access_file':'/dev/null'})

   cherrypy.quickstart(PyServ(), '/', '/opt/t_mon/conf/pyserv.conf')
