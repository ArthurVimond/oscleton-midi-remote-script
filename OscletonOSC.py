import OSC
import socket
import sys
import errno
import traceback

class OscletonOSC(object):

    @staticmethod
    def set_log(func):
        OscletonOSC.log_message = func

    @staticmethod
    def set_message(func):
        OscletonOSC.show_message = func

    @staticmethod
    def release_attributes():
        OscletonOSC.log_message = None
        OscletonOSC.show_message = None

    _in_error = False

    def __init__(self, remotehost = '192.168.0.1', remoteport=9001, localhost='', localport=9000):

        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._socket.setblocking(0)

        self._local_addr = (localhost, localport)
        self._remote_addr = (remotehost, remoteport)
        
        try:
            self._socket.bind(self._local_addr)
            self.log_message('Starting on: ' + str(self._local_addr) + ', remote addr: '+ str(self._remote_addr))
        except:
            self._in_error = True
            msg = 'ERROR: Cannot bind to ' + str(self._local_addr) + ', port in use'
            self.show_message(msg)
            self.log_message(msg)

        self._callback_manager = OSC.CallbackManager()
        self._callback_manager.add('/live/set_peer', self._set_peer)
        self._callback_manager.add('/live/config/discover_ip', self._discover_ip)

    def error(self):
        return self._in_error


    def send(self, address, msg):
        oscmsg = OSC.OSCMessage(address, msg)
        self._socket.sendto(oscmsg.getBinary(), self._remote_addr)

    def send_message(self, message):
        self._socket.sendto(message.getBinary(), self._remote_addr)
    
    
    def process(self):
        try:
            while 1:
                self._data, self._addr = self._socket.recvfrom(65536)

                try:
                    self._callback_manager.handle(self._data, self._addr)

                except OSC.NoSuchCallback, e:
                    errmsg = 'Unknown callback: '+str(e.args[0])
                    self.log_message('Oscleton: '+errmsg)
                    self.send('/live/error', errmsg)

                except Exception, e:
                    errmsg = type(e).__name__+': '+str(e.args[0])
                    tb = sys.exc_info()
                    stack = traceback.extract_tb(tb[2])

                    self.log_message('Oscleton: error handling message ' + errmsg)
                    self.send('/live/error', errmsg)
                    self.log_message("".join(traceback.format_list(stack)))

        except socket.error, e:
            if e.errno == errno.EAGAIN:
                return
                self.log_message('Oscleton: Socket unavailable')

        except Exception, e:
            self.log_message('Oscleton: error handling message '+type(e).__name__+':'+str(e.args[0]))



    def shutdown(self):
        self._socket.close()


    def _set_peer(self, msg, source):
        host = msg[2]
        if host == '':
            host = source[0]
        port = msg[3]
        self.log_message('Oscleton: reconfigured to send to ' + host + ':' + str(port))
        self._remote_addr = (host, port)
        self.send('/live/set_peer/success', True)

    def _discover_ip(self, msg, source):
        host = msg[2]
        if host == '':
            host = source[0]
        port = msg[3]

        # Send back the computer IP
        computer_ip = msg[4]

        self.log_message('Oscleton: IP discovered with success for ' + host + ':' + str(port))
        self._remote_addr = (host, port)
        self.send('/live/config/discover_ip/success', computer_ip)
        