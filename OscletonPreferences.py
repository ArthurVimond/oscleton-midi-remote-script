from .OscletonMixin import OscletonMixin

import os
import json

class OscletonPreferences(OscletonMixin):
    
    def __init__(self):

        self.add_callback('/live/config/app_track', self.set_app_track)
        self.add_callback('/live/config/app_platform', self.set_app_platform)

        self._oscletonDirPath = os.path.expanduser("~/Documents/Oscleton")
        self._prefsFilePath = self._oscletonDirPath + "/preferences.json"
        self._prefsFileFullPath = os.path.expanduser(self._prefsFilePath)

        # Create folder if not exists
        if not os.path.exists(self._oscletonDirPath):
            os.makedirs(self._oscletonDirPath)
            
        # Create file if not exists
        if not os.path.exists(self._prefsFilePath):
            with open(os.path.expanduser(self._prefsFilePath), 'w') as json_file:
                prefs = {}
                prefs['linkedDeviceIPs'] = []
                prefs['appTrack'] = 'production'
                prefs['appPlatform'] = 'android'
                json.dump(prefs, json_file, indent=4)
        
        # Add missing default entries to existing file (if needed)
        if os.path.exists(self._prefsFilePath):

            # Open json file for reading
            jsonFile = open(self._prefsFileFullPath, "r")
            prefs = json.load(jsonFile)
            jsonFile.close()

            # Check entries default value existence
            try:
                app_track = prefs['appTrack']
            except KeyError:
                prefs['appTrack'] = 'production'

            try:
                app_platform = prefs['appPlatform']
            except KeyError:
                prefs['appPlatform'] = 'android'

            # Write back to file
            jsonFile = open(self._prefsFileFullPath, "w+")
            jsonFile.write(json.dumps(prefs, indent=4))
            jsonFile.close()


    def set_linked_device_ip(self, ip):

        # Open json file for reading
        jsonFile = open(self._prefsFileFullPath, "r")
        prefs = json.load(jsonFile)
        jsonFile.close()

        # Update prefs json
        prefs['linkedDeviceIPs'] = [ip]

        # Write back to file
        jsonFile = open(self._prefsFileFullPath, "w+")
        jsonFile.write(json.dumps(prefs, indent=4))
        jsonFile.close()
    

    def get_linked_device_ip(self):

        with open(self._prefsFilePath) as json_file:
            prefs = json.load(json_file)
            linkedDeviceIPs = prefs['linkedDeviceIPs']
            if len(linkedDeviceIPs) > 0:
                return linkedDeviceIPs[0]
            else:
                return None


    def set_app_track(self, msg):
        app_track = msg[1]

        # Open json file for reading
        jsonFile = open(self._prefsFileFullPath, "r")
        prefs = json.load(jsonFile)
        jsonFile.close()

        # Update prefs json
        prefs['appTrack'] = app_track

        # Write back to file
        jsonFile = open(self._prefsFileFullPath, "w+")
        jsonFile.write(json.dumps(prefs, indent=4))
        jsonFile.close()


    def get_app_track(self):
        with open(self._prefsFilePath) as json_file:
            prefs = json.load(json_file)
            app_track = prefs['appTrack']
            return app_track


    def set_app_platform(self, msg):
        app_platform = msg[1]

        # Open json file for reading
        jsonFile = open(self._prefsFileFullPath, "r")
        prefs = json.load(jsonFile)
        jsonFile.close()

        # Update prefs json
        prefs['appPlatform'] = app_platform

        # Write back to file
        jsonFile = open(self._prefsFileFullPath, "w+")
        jsonFile.write(json.dumps(prefs, indent=4))
        jsonFile.close()


    def get_app_platform(self):
        with open(self._prefsFilePath) as json_file:
            prefs = json.load(json_file)
            app_track = prefs['appPlatform']
            return app_track