import subprocess, re, sys
import json
import time
from configparser import ConfigParser
import logging

#?########################################### CONFIG ##############################################################

#! file name
fnafr=sys.argv[0].split('.')[0]

##! Config file path
conf_file = fnafr+".conf"

config = ConfigParser()
config.read(conf_file)

clients_list = []
services_dict = {}

try:
    ConfigInfo = config["ConfigInfo"]
    LogInfo = config["LogInfo"]
    ClientInfo = config["ClientInfo"]
except KeyError:
    sys.exit("Error found in the configuration file.")
    
service = ClientInfo["service"]
key = ClientInfo["key"]
status_file = ClientInfo["status_file"]

host = ConfigInfo["host"]
pattern = ConfigInfo["pattern"]
nbr_sec = int(ConfigInfo["nbr_sec"])

#* log file
log_file = LogInfo["log_file"] 

#* errors log file
err_log_file = LogInfo["err_log_file"] 

#?########################################### CONFIG ##############################################################

#! Logging
log = logging.getLogger()
logformat= '%(asctime)s - %(message)s'
log_formatter = logging.Formatter(logformat, datefmt='%d-%b-%y %H:%M:%S')

#! Log info
log_info = logging.FileHandler(log_file, mode='a')
log_info.setLevel(logging.INFO)
log_info.setFormatter(log_formatter)
log.addHandler(log_info)

#! Log errors
log_err = logging.FileHandler(err_log_file, mode='a')
log_err.setLevel(logging.ERROR)
log_err.setFormatter(log_formatter)
log.addHandler(log_err)

log.setLevel(logging.INFO)

#*########################################### FUNCTIONS ################################################################

def get_status(file):
    cmd = subprocess.run(['tail', '-3', file], capture_output=True).stdout.decode().strip().split('\n')
    status1 = cmd[0][-4:].strip()
    status2 = cmd[1][-4:].strip()
    status3 = cmd[2][-4:].strip()
    if status1 == '[+]' and status2 == '[+]' and status3 == '[+]':
        status = '1'
    else: 
        status = '0'
    return status

def sender(zabbix, service, key, value):
    cmd = subprocess.run(['zabbix_sender', '-z', zabbix, '-s', service, '-k', key, '-o', value], capture_output=True).stdout.decode()
    return cmd

#*########################################### FUNCTIONS ################################################################

if __name__ == "__main__":
    try:
        while True:
            log.info(f"Fetching status of {service} service...")
            
            #! get status
            service_status = get_status(status_file)
            response = sender(host, service, key, service_status)

            result = re.search(pattern, response)

            if result:
                result = result.group()
            else:
                log.error(f"{service}: Regex Error")

            if str(result).strip() == 'processed: 1':
                log.info(f"{service}: {str(result).strip()}")
            elif str(result).strip() == 'processed: 0':
                log.error(f"{service}: {str(result).strip()}")
            else:
                log.critical(f"{service}: Unknown Error")
                
            if nbr_sec > 0:
                log.info(f"Sleeping for {nbr_sec} seconds...")
            time.sleep(nbr_sec)
    except Exception as E:
        log.critical(E)
    


