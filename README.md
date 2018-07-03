# t_mon

##Consists of two processes:

### 1) t_mon.py 

Raspberry PI code to use a 1-wire Temperature sensor and execute some Trigger.py [def triggered()] when measured temperature 
exceeds some define value. 

### 2) t_web.py 

Cherrypy code to provide a simple interface to display current temperatures and triggered events and times. 

## Dependencies 

arrow
psutil
cherrypy

## Misc

Sample unit files provided. 
Steps to configure a PI to embedded mode
