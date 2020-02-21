from OscletonMixin import OscletonMixin

import os
import json

class OscletonPreferences(OscletonMixin):
    
    def __init__(self):

        oscletonDirPath = os.path.expanduser("~/Documents/Oscleton")
        prefsFilePath = oscletonDirPath + "/preferences.json"

        # Create folder if not exists
        if not os.path.exists(oscletonDirPath):
            os.makedirs(oscletonDirPath)
            
        # Create file if not exists
        if not os.path.exists(prefsFilePath):
            with open(os.path.expanduser(prefsFilePath), 'w') as json_file:
                prefs = {}
                prefs['linkedDeviceIPs'] = []
                json.dump(prefs, json_file, indent=4)


    def set_linked_device_ip(self, ip):

        oscletonDirPath = os.path.expanduser("~/Documents/Oscleton")
        prefsFilePath = oscletonDirPath + "/preferences.json"
        prefsFileFullPath = os.path.expanduser(prefsFilePath)

        # Open json file for reading
        jsonFile = open(prefsFileFullPath, "r")
        prefs = json.load(jsonFile)
        jsonFile.close()

        # Update prefs json
        prefs['linkedDeviceIPs'] = [ip]

        # Write back to file
        jsonFile = open(prefsFileFullPath, "w+")
        jsonFile.write(json.dumps(prefs, indent=4))
        jsonFile.close()
    

    def get_linked_device_ip(self):
        
        oscletonDirPath = os.path.expanduser("~/Documents/Oscleton")
        prefsFilePath = oscletonDirPath + "/preferences.json"

        with open(prefsFilePath) as json_file:
            prefs = json.load(json_file)
            linkedDeviceIPs = prefs['linkedDeviceIPs']
            if len(linkedDeviceIPs) > 0:
                return linkedDeviceIPs[0]
            else:
                return None