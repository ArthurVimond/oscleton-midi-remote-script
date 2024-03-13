from __future__ import with_statement
from _Framework.ControlSurface import ControlSurface

from .OscletonApplicationComponent import OscletonApplicationComponent
from .OscletonSessionComponent import OscletonSessionComponent
from .OscletonMixerComponent import OscletonMixerComponent
from .OscletonTransportComponent import OscletonTransportComponent
from .OscletonPreferences import OscletonPreferences
from .OscletonUpdater import OscletonUpdater
from .OscletonBrowserComponent import OscletonBrowserComponent
#
from .OscletonMixin import OscletonMixin
from .OSCServer import OSCServer


class Oscleton(ControlSurface):

    # MIDI Remote Script version
    midi_remote_script_version = '1.1.0'

    def __init__(self, c_instance):
        super(Oscleton, self).__init__(c_instance)
        
        with self.component_guard():
            OSCServer.set_message(self.show_message)
            OscletonMixin.set_log(self.log_message)
            self.osc_server = OSCServer(self)
            OscletonMixin.set_osc_server(self.osc_server)

            self._app = OscletonApplicationComponent(1, 1)
            self._app.setMidiRemoteScriptVersion(self.midi_remote_script_version)
            self._mixer = OscletonMixerComponent(1)
            self._session = OscletonSessionComponent(1,1)
            self._session.set_mixer(self._mixer)
            self._transport = OscletonTransportComponent()
            self._prefs = OscletonPreferences()
            self._updater = OscletonUpdater(self._prefs, self.midi_remote_script_version)
            self._browser = OscletonBrowserComponent()

            self.parse()

            # Set remote host from preferences
            linked_device_ip = self._prefs.get_linked_device_ip()
            self.log_message('linked_device_ip: ' + str(linked_device_ip))
            if linked_device_ip is not None and linked_device_ip is not '':
                self.osc_server.set_peer(linked_device_ip)

            self.show_message('Ready')
            self.osc_server.send("/live/start", (True,))

            self._updater.check_for_update()

    def disconnect(self):
        self.osc_server.send("/live/quit", (True,))
        self.osc_server.shutdown()

    def parse(self):
        self.schedule_message(0, self.tick)

    def set_linked_device_ip(self, ip):
        self._prefs.set_linked_device_ip(ip)

    def tick(self):
        """
        Called once per 100ms "tick".
        Live's embedded Python implementation does not appear to support threading,
        and beachballs when a thread is started. Instead, this approach allows long-running
        processes such as the OSC server to perform operations.
        """
        self.osc_server.process()
        self.schedule_message(1, self.tick)