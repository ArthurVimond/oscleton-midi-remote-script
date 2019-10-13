from _Framework.ControlSurfaceComponent import ControlSurfaceComponent
from _Framework.SubjectSlot import subject_slot


from OscletonMixin import OscletonMixin


class OscletonParameterComponent(ControlSurfaceComponent, OscletonMixin):

    def __init__(self, send = False):
        self._is_send = send
        self._parameter = None
        super(OscletonParameterComponent, self).__init__()


    def set_parameter(self, param):
        self._parameter = param
        self._on_value_changed.subject = param


    def set_parameter_value(self, value):
        self._parameter.value = value
    
    
    @subject_slot('value')
    def _on_value_changed(self):
        t = self._parameter.canonical_parent.canonical_parent
        tid, ty = self.track_id_type(t)
        
        if self._is_send:
            s = list(self._parameter.canonical_parent.sends).index(self._parameter)   
            self.send('/live/'+self._track_types[ty]+'send', tid, s, self._parameter.value)
        
        else:

            track_name = self._parameter.canonical_parent.canonical_parent.name

            d = list(self._parameter.canonical_parent.canonical_parent.devices).index(self._parameter.canonical_parent)
            device_name = self._parameter.canonical_parent.canonical_parent.devices[d].name

            p = list(self._parameter.canonical_parent.parameters).index(self._parameter)
            
            param_display_value = self._parameter.str_for_value(self._parameter.value)
            param_value = self._parameter.value
            param_min = self._parameter.min
            param_max = self._parameter.max
            automation_state = self._parameter.automation_state

            self.send('/live/'+self._track_types[ty]+'device/param', tid, d, p, track_name, device_name, str(self._parameter.name), param_display_value, param_value, param_min, param_max, automation_state)
            
