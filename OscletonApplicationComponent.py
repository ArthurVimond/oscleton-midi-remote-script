from _Framework.SessionComponent import SessionComponent
from OscletonMixin import OscletonMixin, wrap_init

class OscletonApplicationComponent(SessionComponent, OscletonMixin):

    script_version = '0.0.0'
    
    @wrap_init
    def __init__(self, *args, **kwargs):
        super(OscletonApplicationComponent, self).__init__(*args, **kwargs)
        self.add_callback('/live/config/live_version', self._live_version)
        self.add_callback('/live/config/script_version', self._script_version)


    def setMidiRemoteScriptVersion(self, script_version) {
        self.script_version = script_version
    }

    # Live version Callback
    def _live_version(self, msg, src):
        """ Get Live version
        """
        major_version = self.application().get_major_version()
        minor_version = self.application().get_minor_version()
        bugfix_version = self.application().get_bugfix_version()

        full_version = `major_version` + "." + `minor_version` + "." + `bugfix_version`

        self.send('/live/config/live_version', full_version)

    # MIDI Remote script version Callback
    def _script_version(self, msg, src):
        """ Get MIDI Remote Script version
        """
        self.send('/live/config/script_version', self.script_version)
