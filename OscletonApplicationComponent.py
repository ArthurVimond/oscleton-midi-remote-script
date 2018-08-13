from _Framework.SessionComponent import SessionComponent
from OscletonMixin import OscletonMixin, wrap_init

class OscletonApplicationComponent(SessionComponent, OscletonMixin):
    
    @wrap_init
    def __init__(self, *args, **kwargs):
        super(OscletonApplicationComponent, self).__init__(*args, **kwargs)
        self.add_callback('/live/config/live_version', self._live_version)



    # Live version Callbacks
    def _live_version(self, msg, src):
        """ Get Live version
        """
        major_version = self.application().get_major_version()
        minor_version = self.application().get_minor_version()
        bugfix_version = self.application().get_bugfix_version()

        full_version = `major_version` + "." + `minor_version` + "." + `bugfix_version`

        self.send('/live/config/live_version', full_version)
