from django.db.models import Count
from hc.cms.models import Test, Result, Host
import socket
import json
import datetime
import subprocess
import sys
import argparse 
import pycurl

def transformSizeToM(size, num):

   if size == 'K':
      return float(num)/1000
   elif size == 'G':
      return float(num)*1000

   return float(num)

def deleteContent(pfile):
    pfile.seek(0)
    pfile.truncate()

def submitLoadToCouch(server, db, jdoc):

   url = '%s/%s' % (server, db)
   headers = {'Content-Type': 'application/json'}
   payload = json.dumps(jdoc) 
   c = pycurl.Curl()
   c.setopt(pycurl.URL, '%s' % url)
   c.setopt(pycurl.HTTPHEADER, ['Accept: application/json', 'Content-Type: application/json'])
   c.setopt(pycurl.VERBOSE, 0)
   c.setopt(pycurl.POST, 1)
   c.setopt(pycurl.POSTFIELDS, payload)
   c.perform()


parser = argparse.ArgumentParser(description="Calculating load on Hammercloud submission node",
                           formatter_class=argparse.ArgumentDefaultsHelpFormatter)

parser.add_argument('-j', '--jsonfile', help="load data json file", type=argparse.FileType('r+'))
parser.add_argument('-s', '--server', help="couch server name to upload load log")
parser.add_argument('-d', '--db', help="couch db name to upload load log")
parser.add_argument('arguments', nargs='+')
parser.set_defaults(jsonfile='/root/HCnodeload.json')
parser.set_defaults(server='http://couchsrv-2.cern.ch:5984')
parser.set_defaults(db='hcload')
args = parser.parse_args()

# --- Loading json file where the load values are stored
try:
   load_json = json.load(args.jsonfile)
except ValueError:
   print "WARNING: Error loading JSON file %s (empty file?) - creating new JSON" % args.jsonfile
   deleteContent(args.jsonfile)
   load_json = []

timestamp = datetime.datetime.now().strftime('%Y/%m/%d - %H:%M:%S')
print timestamp

hn = socket.getfqdn()
host = Host.objects.filter(name=hn)[0]

running_tests    = Test.objects.filter(state='running').filter(host=host).count()
submitting_tests = Test.objects.filter(state='submitting').filter(host=host).count()

totalrunning = 0
for test in Test.objects.filter(state='running').filter(host=host):
   running = test.getResults_for_test.filter(ganga_status='r').count()
   totalrunning += running

totalsubmitted = 0
for test in Test.objects.filter(state='running').filter(host=host):
   submitted = test.getResults_for_test.filter(ganga_status='s').count()
   totalsubmitted += submitted

print "----- Hammercloud test running on %s -----" % hn
print "Running tests:        %s" % running_tests
print "Submitting tests:     %s" % submitting_tests
print "Total running jobs:   %s" % totalrunning
print "Total submitted jobs: %s" % totalsubmitted

# -- Calculating memory usage
mem_used_total = subprocess.Popen("free -m | grep Mem | awk '{print $3}'", shell=True, stdout=subprocess.PIPE).stdout.read().strip('\n')

mem_buffers    = subprocess.Popen("free -m | grep Mem | awk '{print $6}'", shell=True, stdout=subprocess.PIPE).stdout.read().strip('\n')
mem_cached     = subprocess.Popen("free -m | grep Mem | awk '{print $7}'", shell=True, stdout=subprocess.PIPE).stdout.read().strip('\n')
mem_without_bc = subprocess.Popen("free -m | grep 'buffers/cache' | awk '{print $3}'", shell=True, stdout=subprocess.PIPE).stdout.read().strip('\n')

mem_used_process = subprocess.Popen("python /root/ps_mem.py", shell=True, stdout=subprocess.PIPE).stdout.read()
size_mem_used_process = mem_used_process.split('\n')[-3].lstrip(' ').split(' ')[1][0] # (K)ib, (M)ib or (G)ib
mem_used_process = mem_used_process.split('\n')[-3].lstrip(' ').split(' ')[0] # only taking total value
mem_used_process = transformSizeToM(size_mem_used_process, mem_used_process)

# ----- Calculating mem used by Hammercloud python process

pids_string = ""

# getting python process pids
pids = subprocess.Popen("ps auxf | grep python | grep /data/hc | grep -v grep | awk '{print $2}'", shell=True, stdout=subprocess.PIPE).stdout.read()
pids = filter(lambda x: x != "", pids.split('\n'))
for pid in pids:
   pids_string += "%s," % pid
pids_string = pids_string.rstrip(',')
if pids_string:
   # calling /root/ps_mem.py with pids as argument
   python_mem = subprocess.Popen("python /root/ps_mem.py -p %s" % pids_string, shell=True, stdout=subprocess.PIPE).stdout.read()
   size_python_mem = python_mem.split('\n')[-3].lstrip(' ').split(' ')[1][0] # (K)ib, (M)ib or (G)ib
   python_mem = python_mem.split('\n')[-3].lstrip(' ').split(' ')[0] # only taking total value
   python_mem = transformSizeToM(size_python_mem, python_mem)
else:
   python_mem = 0

# ----- Calculating mem used by Hammercloud shell process

pids_string = ""

# getting shell process pids
pids = subprocess.Popen("ps auxf | grep sh | grep /data/hc | grep -v grep | grep -v python | awk '{print $2}'", shell=True, stdout=subprocess.PIPE).stdout.read()
pids = filter(lambda x: x != "", pids.split('\n'))
for pid in pids:
   pids_string += "%s," % pid
pids_string = pids_string.rstrip(',')
if pids_string:
   # calling /root/ps_mem.py with pids as argument
   shell_mem = subprocess.Popen("python /root/ps_mem.py -p %s" % pids_string, shell=True, stdout=subprocess.PIPE).stdout.read()
   size_shell_mem = shell_mem.split('\n')[-3].lstrip(' ').split(' ')[1][0] # (K)ib, (M)ib or (G)ib
   shell_mem = shell_mem.split('\n')[-3].lstrip(' ').split(' ')[0] # only taking total value
   shell_mem = transformSizeToM(size_shell_mem, shell_mem)
else:
   shell_mem = 0

# -- Calculating cpu usage

total_cpu_load = open('/proc/loadavg', 'r').readline().strip('\n')

# -- Calculating I/O

wa = subprocess.Popen("top -n 1 -b | grep 'Cpu(s):' | awk '{print $6}'", shell=True, stdout=subprocess.PIPE).stdout.read().strip('\n').split('%')[0]

print "---- Memory stats ----"
print "Total memory used:                      %s Mb" % mem_used_total
print "Total memory used by process:           %s Mib" % mem_used_process
print "Total memory used by HC python process: %s Mib" % python_mem
print "Total memory used by HC shell process:  %s Mib" % shell_mem
print "---- CPU stats ----"
print "Avgload: %s" % total_cpu_load



current_load = {"timestamp": int(datetime.datetime.now().strftime('%s')),
                "hostname": hn,
                "running_tests": int(running_tests),
                "submitting_tests": int(submitting_tests),
                "tot_running_jobs": int(totalrunning),
                "tot_queued_jobs": int(totalsubmitted),
                "mem_buffers": float(mem_buffers),
                "mem_cached": float(mem_cached),
                "mem_without_bc": float(mem_without_bc),
                "used_mem": float(mem_used_total),
                "used_mem_proc": float(mem_used_process),
                "used_mem_HCpythonproc": float(python_mem),
                "used_mem_HCshellproc": float(shell_mem),
                "cpu_load_5": float(total_cpu_load.split()[0]),
                "cpu_load_10": float(total_cpu_load.split()[1]),
                "cpu_load_15": float(total_cpu_load.split()[2]),
                "wa": float(wa)}

submitLoadToCouch(args.server, args.db, current_load)

#load_json.append(current_load)
#deleteContent(args.jsonfile)
#json.dump(load_json, args.jsonfile)

