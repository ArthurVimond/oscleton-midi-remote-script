import Live
from _Framework.ChannelStripComponent import ChannelStripComponent
from _Framework.SubjectSlot import subject_slot

from .OscletonDeviceComponent import OscletonDeviceComponent
from .OscletonMixin import OscletonMixin, wrap_init
from .OscletonParameterComponent import OscletonParameterComponent


class OscletonChannelStripComponent(ChannelStripComponent, OscletonMixin):
    @wrap_init
    def __init__(self, *a, **kw):
        self._track_id = None
        self._type = None
        self._devices = []
        self._sends = []

        super(OscletonChannelStripComponent, self).__init__(*a, **kw)

        self.set_default('_track_id')

        self.add_callback('/live/track/stop', self._stop)

        for t in self._track_types:
            self.add_callback('/live/' + t + 'crossfader', self._crossfader)

        for ty in ['track', 'return']:
            self.add_simple_callback('/live/' + ty + '/name', '_track', 'name', self._is_track,
                                     getattr(self, '_on_track_name_changed'))
            self.add_simple_callback('/live/' + ty + '/color', '_track', 'color', self._is_track,
                                     getattr(self, '_on_track_color_changed'))

        self.add_callback('/live/track/state', self._track_state)

        for ty in self._track_types:
            self.add_callback('/live/' + ty + 'devices', self._device_list)
            self.add_callback('/live/' + ty + 'select', self._view)

    def with_track(fn):
        def decorator(*a, **kw):
            if self._track is not None:
                fn(*a, **kw)

        return decorator

    @property
    def id(self):
        if self._track is not None:
            return self._track_id
        else:
            return -1

    def _get_name(self):
        if self._track is not None:
            return self._track.name
        else:
            return ''

    def _set_name(self, name):
        if self._track is not None:
            self._track.name = name

    track_name = property(_get_name, _set_name)

    def disconnect(self):
        super(OscletonChannelStripComponent, self).disconnect()

    def _is_track(self, msg):
        if 'return' in msg[0]:
            ty = 1
        elif 'master' in msg[0]:
            ty = 2
        else:
            ty = 0
        check_id = msg[1] == self._track_id if ty != 2 else True
        return ty == self._type and check_id

    def set_track(self, track):
        if self._is_enabled_ovr:
            self._track_id, self._type = self.track_id_type(track)
            super(OscletonChannelStripComponent, self).set_track(track)

            self._on_device_list_changed.subject = track
            self._on_track_color_changed.subject = track
            self._on_track_state_changed.subject = track

            m = track.mixer_device if track else None
            self._on_volume_changed.subject = m.volume if track else None
            self._on_panning_changed.subject = m.panning if track else None

            self._lo2__on_sends_changed()
            self._on_device_list_changed()

    def _lo2__on_sends_changed(self):
        if self._track is not None and self._type != 2:
            diff = len(self._track.mixer_device.sends) - len(self._sends)

            if diff > 0:
                for i in range(diff):
                    self._sends.append(OscletonParameterComponent(True))

            if diff < 0:
                for i in range(len(self._sends) - 1, len(self._track.mixer_device.sends) - 1, -1):
                    self._sends[i].disconnect()
                    self._sends.remove(self._sends[i])

            for i, s in enumerate(self._sends):
                s.set_parameter(self._track.mixer_device.sends[i])

    @subject_slot('devices')
    def _on_device_list_changed(self):
        if self._track is not None:
            diff = len(self._track.devices) - len(self._devices)

            if diff > 0:
                for i in range(diff):
                    self._devices.append(OscletonDeviceComponent())

            if diff < 0:
                for i in range(len(self._devices) - 1, len(self._track.devices) - 1, -1):
                    self._devices[i].disconnect()
                    self._devices.remove(self._devices[i])

            for i, dc in enumerate(self._devices):
                dc.set_device(self._track.devices[i])

            self._send_device_list()

    @subject_slot('value')
    def _on_volume_changed(self):
        self.send_default('/live/' + self._track_types[self._type] + 'volume', self._track.name,
                          self._track.mixer_device.volume.value)

    @subject_slot('value')
    def _on_panning_changed(self):
        self.send_default('/live/' + self._track_types[self._type] + 'panning', self._track.name,
                          self._track.mixer_device.panning.value)

    # Callbacks
    def _on_mute_changed(self):
        if self._type is not None and self._type < 2:
            self.send_default('/live/' + self._track_types[self._type] + 'mute', self._track.name, self._track.mute)

    def _on_solo_changed(self):
        if self._type is not None and self._type < 2:
            self.send_default('/live/' + self._track_types[self._type] + 'solo', self._track.name, self._track.solo)

    def _on_arm_changed(self):
        if self._type is not None and self._type == 0 and self._track.can_be_armed:
            self.send_default('/live/' + self._track_types[self._type] + 'arm', self._track.name, self._track.arm)

    def _on_track_name_changed(self):
        if self._type is not None:
            self.send_default('/live/' + self._track_types[self._type] + 'name', self._track.name)

    def _on_cf_assign_changed(self):
        if self._type is not None and self._type < 2:
            self.send_default('/live/' + self._track_types[self._type] + 'crossfader',
                              self._track.mixer_device.crossfade_assign)

    # On track rename this is triggered, causing _on_arm_changed to be triggered
    def _on_input_routing_changed(self):
        pass

    @subject_slot('color')
    def _on_track_color_changed(self):
        self.send_default('/live/' + self._track_types[self._type] + 'color', self._track.color)

    @subject_slot('playing_slot_index')
    def _on_track_state_changed(self):
        self.send_default('/live/track/state', self._track.playing_slot_index)

    # @with_track
    def _device_list(self, msg):
        if self._is_track(msg) and self._track is not None:
            self._send_device_list()

    def _send_device_list(self):
        devices = []
        for i, d in enumerate(self._track.devices):
            devices.append(i)
            devices.append(d.name)

        if self._type == 2:
            self.send('/live/' + self._track_types[self._type] + 'devices', *devices)
        else:
            self.send_default('/live/' + self._track_types[self._type] + 'devices', *devices)

    def _stop(self, msg):
        if self._track is not None and self._is_track(msg):
            self._track.stop_all_clips()

    def _track_state(self, msg):
        if self._is_track(msg):
            self._on_track_state_changed()

    def _view(self, msg):
        if self._is_track(msg) and self._track is not None:
            self.song().view.selected_track = self._track

    def _crossfader(self, msg):
        if self._is_track(msg) and self._track is not None:
            # Master
            if self._type == 2:
                self._track.mixer_device.crossfader.value = msg[2]

            # Assign xfader
            else:
                v = msg[3] if len(msg) == 4 else None
                if v is not None:
                    if v == 0:
                        self._track.mixer_device.crossfade_assign = Live.MixerDevice.MixerDevice.crossfade_assignments.A
                    elif v == 1:
                        self._track.mixer_device.crossfade_assign = Live.MixerDevice.MixerDevice.crossfade_assignments.NONE
                    elif v == 2:
                        self._track.mixer_device.crossfade_assign = Live.MixerDevice.MixerDevice.crossfade_assignments.B
                else:
                    self._on_cf_assign_changed()
