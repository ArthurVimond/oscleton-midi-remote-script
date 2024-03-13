from _Framework.MixerComponent import MixerComponent

from .OscletonChannelStripComponent import OscletonChannelStripComponent
from .OscletonMixin import OscletonMixin, wrap_init


class OscletonMixerComponent(MixerComponent, OscletonMixin):

    @wrap_init
    def __init__(self, *a, **kw):
        self._track_count = 0
        super(OscletonMixerComponent, self).__init__(12, 12, *a, **kw)

        self.add_callbacks()

        self.add_callback('/live/track/name/block', self._track_name_block)

        self.add_function_callback('/live/tracks', self._lo2_on_track_list_changed)
        self._selected_strip.set_track(None)
        self._selected_strip.set_is_enabled(False)

        self._register_timer_callback(self._update_mixer_vols)

    def add_callbacks(self):
        for t in [0, 1]:
            for p in ['mute', 'solo', 'arm']:
                self.add_mixer_callback('/live/' + self._track_types[t] + p, p)
            for p in ['volume', 'panning', 'send']:
                self.add_mixer_callback('/live/' + self._track_types[t] + p, p, 1)

        self.add_mixer_callback('/live/master/volume', 'volume', 1)
        self.add_mixer_callback('/live/master/pan', 'pan', 1)

        for ty in self._track_types:
            self.add_device_param_callback('/live/' + ty + 'device/param')

    def add_mixer_callback(self, addr, property, mixer=0):
        def cb(msg):
            if len(msg) == 3:
                v = msg[2]
            elif len(msg) == 4:
                v = msg[3]
            else:
                v = None

            track_index = msg[1]

            if property is not 'send':
                track = self._track(addr, track_index)

                obj = getattr(track.mixer_device, property) if mixer else track
                pr = 'value' if mixer else property
                ot = float if mixer else int
                if v is not None:
                    setattr(obj, pr, v)
                else:
                    if self._type == 2:
                        self.send('/live/master/' + property, ot(getattr(obj, pr)))
                    else:
                        self.send_default('/live/' + self._track_types[self._type] + property,
                                          ot(getattr(obj, pr)))
            else:
                # Sends
                track = self._track(addr, track_index)
                send_id = msg[2]
                send_value = msg[3]
                send = track.mixer_device.sends[send_id]
                send.value = send_value

        self.add_callback(addr, cb)

    def add_device_param_callback(self, addr):
        def cb(msg):
            track_index = msg[1]
            device_index = msg[2]
            param_index = msg[3]
            value = msg[4]

            track = self._track(addr, track_index)
            device = track.devices[device_index]
            param = device.parameters[param_index]
            param.value = value

        self.add_callback(addr, cb)

    def _track(self, addr, track_index):
        if 'master' in addr:
            track = self.song().master_track
        elif 'return' in addr:
            track = self.song().return_tracks[track_index]
        else:
            track = self.song().visible_tracks[track_index]
        return track

    def _update_mixer_vols(self):
        pass

    def _create_strip(self):
        return OscletonChannelStripComponent()

    def _reassign_tracks(self):
        self.log_message('reassigning tracks')
        diff = len(self.tracks_to_use()) - len(self._channel_strips)

        if diff > 0:
            for i in range(diff):
                self._channel_strips.append(self._create_strip())

        if diff < 0:
            for i in range(len(self._channel_strips) - 1, len(self.tracks_to_use()) - 1, -1):
                self._channel_strips[i].disconnect()
                self._channel_strips.remove(self._channel_strips[i])

        for i, cs in enumerate(self._channel_strips):
            cs.set_track(self.tracks_to_use()[i])

        # Return tracks
        returns = self.song().return_tracks
        for index in range(len(self._return_strips)):
            if len(returns) > index:
                self._return_strips[index].set_track(returns[index])
            else:
                self._return_strips[index].set_track(None)

    def _lo2__on_return_tracks_changed(self):
        self._reassign_tracks()

    # Callbacks
    def _lo2_on_track_list_changed(self):
        if len(self.song().tracks) != self._track_count:
            self.log_message('/live/tracks:' + str(len(self.song().tracks)))
            self.send('/live/tracks', len(self.song().tracks))
            self._track_count = len(self.song().tracks)

    def _lo2_on_selected_track_changed(self):
        id, type = self.track_id_type(self.song().view.selected_track)

        self.send('/live/track/select', type, id)

    # Track Callbacks
    def _track_name_block(self, msg):
        """
        Gets block of scene names
        """
        b = []
        for i in range(msg[2], msg[2] + msg[3]):
            if i < len(self._channel_strips):
                t = self.channel_strip(i)
                b.append(i, t.track_name)
            else:
                b.append(i, '')

        self.send('/live/track/name/block', b)
