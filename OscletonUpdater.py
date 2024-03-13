from _Framework.SessionComponent import SessionComponent
from OscletonMixin import OscletonMixin

import os
import json
import urllib2
import zipfile
import platform

class OscletonUpdater(SessionComponent, OscletonMixin):
    
    def __init__(self, prefs, midi_remote_script_version):
        self.ableton_dirs = []
        
        self._prefs = prefs
        self._midi_remote_script_version = midi_remote_script_version

    def check_for_update(self):

        # Get OS
        self._os = platform.system() # Windows, Linux or Darwin

        app_track = self._prefs.get_app_track()
        app_platform = self._prefs.get_app_platform()

        oscleton_api_base_url = 'https://api.oscleton.com/'
        latest_script_api_url = oscleton_api_base_url + 'v1/midi-remote-scripts/latest' + '?platform=' + app_platform + '&track=' + app_track + '&pythonVersion=2'

        need_update = False

        # Check if need to update Oscleton MIDI Remote Script
        try:
            request = urllib2.Request(latest_script_api_url)
            response = urllib2.urlopen(request, timeout=5.0).read()
            response_json = json.loads(response)
            latest_midi_remote_script_version = response_json['midiRemoteScriptVersion']
            need_update = self.map_to_version_code_int(latest_midi_remote_script_version) > self.map_to_version_code_int(self._midi_remote_script_version)

        except Exception, e:
            self.log_message('latest_script_api_url request exception: ' + str(e))

        if need_update == True:

            # Download the Oscleton MIDI Remote Script and save it to the temp Documents/Oscleton directory
            oscleton_dir_path = os.path.expanduser("~/Documents/Oscleton")
            script_file_path = oscleton_dir_path + "/oscleton.zip"
            url = 'https://oscleton.com/download/midi-remote-script/python2/' + latest_midi_remote_script_version + '/oscleton.zip'
            self.log_message('Downloading latest Oscleton MIDI Remote Script: ' + latest_midi_remote_script_version)

            try:
                file_data = urllib2.urlopen(url)
                data_to_write = file_data.read()
        
                with open(script_file_path, 'wb') as f:
                    f.write(data_to_write)

                # Find Ableton Live directory
                live_major_version = str(self.application().get_major_version())
                if self._os == "Darwin":
                    files = os.listdir('/Applications')
                    for name in files:
                        if ('Ableton Live ' + live_major_version) in name:
                            self.ableton_dirs.append(name)

                            # Unzip the script to the MIDI Remote Scripts folder
                            for ableton_dir in self.ableton_dirs:
                                with zipfile.ZipFile(script_file_path, 'r') as zip_ref:
                                    zip_ref.extractall('/Applications/' + ableton_dir + '/Contents/App-Resources/MIDI Remote Scripts')
                
                elif self._os == "Windows":
                    files = os.listdir('C:\ProgramData\Ableton')
                    for name in files:
                        if ('Live ' + live_major_version) in name:
                                self.ableton_dirs.append(name)

                                # Unzip the script to the MIDI Remote Scripts folder
                                for ableton_dir in self.ableton_dirs:
                                    with zipfile.ZipFile(script_file_path, 'r') as zip_ref:
                                        zip_ref.extractall('C:\ProgramData\Ableton\\' + ableton_dir + '\Resources\MIDI Remote Scripts')
            
            except Exception, e:
                self.log_message('Download latest Oscleton MIDI Remote Script exception: ' + str(e))


    def map_to_version_code_int(self, version):
        l = [int(x, 10) for x in version.split('.')]
        l.reverse()
        version = sum(x * (100 ** i) for i, x in enumerate(l))
        return version
        
    