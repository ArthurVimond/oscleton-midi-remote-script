from __future__ import with_statement
from _Framework.ControlSurface import ControlSurface

from OscletonApplicationComponent import OscletonApplicationComponent
from OscletonSessionComponent import OscletonSessionComponent
from OscletonMixerComponent import OscletonMixerComponent
from OscletonTransportComponent import OscletonTransportComponent

from OscletonMixin import OscletonMixin
from OscletonOSC import OscletonOSC


class Oscleton(ControlSurface):

    # MIDI Remote Script version
    midi_remote_script_version = '0.2.0'


    def __init__(self, c_instance):
        super(Oscleton, self).__init__(c_instance)
        
        with self.component_guard():
            OscletonOSC.set_log(self.log_message)
            OscletonOSC.set_message(self.show_message)
            self.osc_handler = OscletonOSC()
            
            OscletonMixin.set_osc_handler(self.osc_handler)
            OscletonMixin.set_log(self.log_message)
            
            self._app = OscletonApplicationComponent(1, 1)
            self._app.setMidiRemoteScriptVersion(self.midi_remote_script_version)
            self._mixer = OscletonMixerComponent(1)
            self._session = OscletonSessionComponent(1,1)
            self._session.set_mixer(self._mixer)
            self._transport = OscletonTransportComponent()
            
            self.parse()

            if not self.osc_handler.error():
                self.show_message('Ready')
                self.osc_handler.send('/live/startup', 1)


    def disconnect(self):
        self.osc_handler.shutdown()


    def parse(self):
        self.osc_handler.process()
        self.schedule_message(1, self.parse)