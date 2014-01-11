# -*- coding: utf-8 -*-
import threading
import logging
import time
import select
import socket
import ssl
import struct

from errors import *
from constants import *
import users
import channels
import blobs
import commands
import messages
import callbacks
import tools
import soundoutput

import mumble_pb2

from pycelt import SUPPORTED_BITSTREAMS

class Mumble(threading.Thread):
    """
    Mumble client library main object.
    basically a thread
    """
    def __init__(self, host=None, port=None, user=None, password=None, client_certif=None, reconnect=False, debug=False):
        """
        host=mumble server hostname or address
        port=mumble server port
        user=user to use for the connection
        password=password for the connection
        client_certif=client certificate to authenticate the connection (NOT IMPLEMENTED)
        reconnect=if True, try to reconnect if disconnected
        debug=if True, send debugging messages (lot of...) to the stdout
        """
#TODO: client certificate authentication
#TODO: exit both threads properly
#TODO: use UDP audio
        threading.Thread.__init__(self)
        
        self.Log = logging.getLogger("PyMumble")  # logging object for errors and debugging
        if debug:
            self.Log.setLevel(logging.DEBUG)
        else:
            self.Log.setLevel(logging.ERROR)
            
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s-%(name)s-%(levelname)s-%(message)s')
        ch.setFormatter(formatter)
        self.Log.addHandler(ch)
        
        self.parent_thread = threading.current_thread()  # main thread of the calling application
        self.mumble_thread = None  # thread of the mumble client library
        
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.client_certif = client_certif
        self.reconnect = reconnect
        
        self.receive_sound = False  # set to True to treat incoming audio, otherwise it is simply ignored
        
        self.loop_rate = PYMUMBLE_LOOP_RATE
        
        self.application = PYMUMBLE_VERSION_STRING

        self.callbacks = callbacks.CallBacks()  #callbacks management

        self.ready_lock = threading.Lock()  # released when the connection is fully established with the server
        self.ready_lock.acquire()
        
    def init_connection(self):
        """Initialize variables that are local to a connection, (needed if the client automatically reconnect)"""
        self.ready_lock.acquire(False)  # reacquire the ready-lock in case of reconnection
        
        self.connected = PYMUMBLE_CONN_STATE_NOT_CONNECTED
        self.control_socket = None
        self.media_socket = None  # Not implemented - for UDP media
        
        self.bandwidth = PYMUMBLE_BANDWIDTH  # reset the outgoing bandwidth to it's default before connectiong
        self.server_max_bandwidth = None
        self.udp_active = False
        
        self.users = users.Users(self, self.callbacks)  # contain the server's connected users informations
        self.channels = channels.Channels(self, self.callbacks)  # contain the server's channels informations
        self.blobs = blobs.Blobs(self)  # manage the blob objects
        self.sound_output = soundoutput.SoundOutput(self, PYMUMBLE_AUDIO_PER_PACKET, self.bandwidth)  # manage the outgoing sounds
        self.commands = commands.Commands()  # manage commands sent between the main and the mumble threads
        
        self.receive_buffer = ""  # initialize the control connection input buffer
        
    def run(self):
        """Connect to the server and start the loop in its thread.  Retry if requested"""
        self.mumble_thread = threading.current_thread()
        
        # loop if auto-reconnect is requested
        while True:
            self.init_connection()  # reset the connection-specific object members
            
            self.connect()
            
            self.loop()
        
            if not self.reconnect or not self.parent_thread.is_alive():
                break
            
            time.sleep(PYMUMBLE_CONNECTION_RETRY_INTERVAL)
        
    def connect(self):
        """Connect to the server"""
        
        # Connect the SSL tunnel
        self.Log.debug("connecting to %s on port %i.", self.host, self.port)
        std_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.control_socket = ssl.wrap_socket(std_sock, certfile=self.client_certif, ssl_version=ssl.PROTOCOL_TLSv1)

        self.control_socket.connect((self.host, self.port))
        
        self.control_socket.setblocking(0)
        
        # Perform the Mumble authentication
        version = mumble_pb2.Version()
        version.version = (PYMUMBLE_PROTOCOL_VERSION[0] << 16) + (PYMUMBLE_PROTOCOL_VERSION[1] << 8) + PYMUMBLE_PROTOCOL_VERSION[2]
        version.release = self.application
        version.os = PYMUMBLE_OS_STRING
        version.os_version = PYMUMBLE_OS_VERSION_STRING
        self.Log.debug("sending: version: %s", version)
        self.send_message(PYMUMBLE_MSG_TYPES_VERSION, version)
        
        authenticate = mumble_pb2.Authenticate()
        authenticate.username = self.user
        authenticate.password = self.password
        authenticate.celt_versions.extend(SUPPORTED_BITSTREAMS.keys())
#        authenticate.celt_versions.extend([-2147483637])  # for debugging - only celt 0.7
        authenticate.opus = True
        self.Log.debug("sending: authenticate: %s", authenticate)
        self.send_message(PYMUMBLE_MSG_TYPES_AUTHENTICATE, authenticate)
        
        self.connected = PYMUMBLE_CONN_STATE_AUTHENTICATING
        
    def loop(self):
        """
        Main loop
        waiting for a message from the server for maximum self.loop_rate time
        take care of sending the ping
        take care of sending the queued commands to the server
        check on every iteration for outgoing sound 
        check for disconnection
        """
        self.Log.debug("entering loop")
        
        last_ping = time.time()  # keep track of the last ping time
        
        # loop as long as the connection and the parent thread are alive
        while self.connected != PYMUMBLE_CONN_STATE_NOT_CONNECTED and self.parent_thread.is_alive():
            if last_ping + PYMUMBLE_PING_DELAY <= time.time():  # when it is time, send the ping
                self.ping()
                last_ping = time.time()

            if self.connected == PYMUMBLE_CONN_STATE_CONNECTED:
                while self.commands.is_cmd():
                    self.treat_command(self.commands.pop_cmd())  # send the commands coming from the application to the server
                    
                self.sound_output.send_audio()  # send outgoing audio if available
            
            (rlist, wlist, xlist) = select.select([self.control_socket], [], [self.control_socket], self.loop_rate)  # wait for a socket activity
            
            if self.control_socket in rlist:  # something to be read on the control socket
                self.read_control_messages()
            elif self.control_socket in xlist:  # socket was closed
                self.control_socket.close()
                self.connected = PYMUMBLE_CONN_STATE_NOT_CONNECTED
                
    def ping(self):
        """Send the keepalive through available channels"""
#TODO: Ping counters        
        ping = mumble_pb2.Ping()
        ping.timestamp=int(time.time())
        self.Log.debug("sending: ping: %s", ping)
        self.send_message(PYMUMBLE_MSG_TYPES_PING, ping)
    
    def send_message(self, type, message):
        """Send a control message to the server"""
        packet=struct.pack("!HL", type, message.ByteSize()) + message.SerializeToString()

        while len(packet)>0:
            self.Log.debug("sending message")
            sent=self.control_socket.send(packet)
            if sent < 0:
                raise socket.error("Server socket error")
            packet=packet[sent:]
            
    def read_control_messages(self):
        """Read control messages coming from the server"""
#        from tools import toHex  # for debugging
        
        buffer = self.control_socket.recv(PYMUMBLE_READ_BUFFER_SIZE)
        self.receive_buffer += buffer

        while len(self.receive_buffer) >= 6:  # header is present (type + length)
            self.Log.debug("read control connection")
            header = self.receive_buffer[0:6]
            (type, size) = struct.unpack("!HL", header)  # decode header

            if len(self.receive_buffer) < size+6:  # if not length data, read further
                break
            
#            self.Log.debug("message received : " + toHex(self.receive_buffer[0:size+6]))  # for debugging
            
            message = self.receive_buffer[6:size+6]  # get the control message
            self.receive_buffer = self.receive_buffer[size+6:]  # remove from the buffer the read part
        
            self.dispatch_control_message(type, message)
            
    def dispatch_control_message(self, type, message):
        """Dispatch control messages based on their type"""
        self.Log.debug("dispatch control message")
        if type == PYMUMBLE_MSG_TYPES_UDPTUNNEL:  # audio encapsulated in control message
            self.sound_received(message)
            
        elif type == PYMUMBLE_MSG_TYPES_VERSION:
            mess = mumble_pb2.Version()
            mess.ParseFromString(message)
            self.Log.debug("message: Version : %s", mess)
            
        elif type == PYMUMBLE_MSG_TYPES_AUTHENTICATE:
            mess = mumble_pb2.Authenticate()
            mess.ParseFromString(message)
            self.Log.debug("message: Authenticate : %s", mess)
            
        elif type == PYMUMBLE_MSG_TYPES_PING:
            mess = mumble_pb2.Ping()
            mess.ParseFromString(message)
            self.Log.debug("message: Ping : %s", mess)
            
        elif type == PYMUMBLE_MSG_TYPES_REJECT:
            mess = mumble_pb2.Reject()
            mess.ParseFromString(message)
            self.Log.debug("message: reject : %s", mess)
            self.ready_lock.release()
            raise ConnectionRejectedError(mess.reason)
        
        elif type == PYMUMBLE_MSG_TYPES_SERVERSYNC:  # this message finish the connection process
            mess = mumble_pb2.ServerSync()
            mess.ParseFromString(message)
            self.Log.debug("message: serversync : %s", mess)
            self.users.set_myself(mess.session)
            self.server_max_bandwidth = mess.max_bandwidth 
            self.set_bandwidth(mess.max_bandwidth)
            
            if self.connected == PYMUMBLE_CONN_STATE_AUTHENTICATING:
                self.connected = PYMUMBLE_CONN_STATE_CONNECTED
                self.callbacks(PYMUMBLE_CLBK_CONNECTED)
                self.ready_lock.release()  # release the ready-lock

        elif type == PYMUMBLE_MSG_TYPES_CHANNELREMOVE:
            mess = mumble_pb2.ChannelRemove()
            mess.ParseFromString(message)
            self.Log.debug("message: ChannelRemove : %s", mess)
            
            self.channels.remove(mess.channel_id)
            
        elif type == PYMUMBLE_MSG_TYPES_CHANNELSTATE:
            mess = mumble_pb2.ChannelState()
            mess.ParseFromString(message)
            self.Log.debug("message: channelstate : %s", mess)
            
            self.channels.update(mess)
            
        elif type == PYMUMBLE_MSG_TYPES_USERREMOVE:
            mess = mumble_pb2.UserRemove()
            mess.ParseFromString(message)
            self.Log.debug("message: UserRemove : %s", mess)
            
            self.users.remove(mess)
            
        elif type == PYMUMBLE_MSG_TYPES_USERSTATE:
            mess = mumble_pb2.UserState()
            mess.ParseFromString(message)
            self.Log.debug("message: userstate : %s", mess)
            
            self.users.update(mess)
            
        elif type == PYMUMBLE_MSG_TYPES_BANLIST:
            mess = mumble_pb2.BanList()
            mess.ParseFromString(message)
            self.Log.debug("message: BanList : %s", mess)
            
        elif type == PYMUMBLE_MSG_TYPES_TEXTMESSAGE:
            mess = mumble_pb2.TextMessage()
            mess.ParseFromString(message)
            self.Log.debug("message: TextMessage : %s", mess)

            self.callbacks(PYMUMBLE_CLBK_TEXTMESSAGERECEIVED, mess.message)
            
        elif type == PYMUMBLE_MSG_TYPES_PERMISSIONDENIED:
            mess = mumble_pb2.PermissionDenied()
            mess.ParseFromString(message)
            self.Log.debug("message: PermissionDenied : %s", mess)
            
        elif type == PYMUMBLE_MSG_TYPES_ACL:
            mess = mumble_pb2.ACL()
            mess.ParseFromString(message)
            self.Log.debug("message: ACL : %s", mess)
            
        elif type == PYMUMBLE_MSG_TYPES_QUERYUSERS:
            mess = mumble_pb2.QueryUsers()
            mess.ParseFromString(message)
            self.Log.debug("message: QueryUsers : %s", mess)
            
        elif type == PYMUMBLE_MSG_TYPES_CRYPTSETUP:
            mess = mumble_pb2.CryptSetup()
            mess.ParseFromString(message)
            self.Log.debug("message: CryptSetup : %s", mess)
            
        elif type == PYMUMBLE_MSG_TYPES_CONTEXTACTIONADD:
            mess = mumble_pb2.ContextActionAdd()
            mess.ParseFromString(message)
            self.Log.debug("message: ContextActionAdd : %s", mess)
            
        elif type == PYMUMBLE_MSG_TYPES_CONTEXTACTION:
            mess = mumble_pb2.ContextActionAdd()
            mess.ParseFromString(message)
            self.Log.debug("message: ContextActionAdd : %s", mess)
            
        elif type == PYMUMBLE_MSG_TYPES_USERLIST:
            mess = mumble_pb2.UserList()
            mess.ParseFromString(message)
            self.Log.debug("message: UserList : %s", mess)
            
        elif type == PYMUMBLE_MSG_TYPES_VOICETARGET:
            mess = mumble_pb2.VoiceTarget()
            mess.ParseFromString(message)
            self.Log.debug("message: VoiceTarget : %s", mess)
            
        elif type == PYMUMBLE_MSG_TYPES_PERMISSIONQUERY:
            mess = mumble_pb2.PermissionQuery()
            mess.ParseFromString(message)
            self.Log.debug("message: PermissionQuery : %s", mess)
            
        elif type == PYMUMBLE_MSG_TYPES_CODECVERSION:
            mess = mumble_pb2.CodecVersion()
            mess.ParseFromString(message)
            self.Log.debug("message: CodecVersion : %s", mess)
            
            self.sound_output.set_default_codec(mess)
            
        elif type == PYMUMBLE_MSG_TYPES_USERSTATS:
            mess = mumble_pb2.UserStats()
            mess.ParseFromString(message)
            self.Log.debug("message: UserStats : %s", mess)
            
        elif type == PYMUMBLE_MSG_TYPES_REQUESTBLOB:
            mess = mumble_pb2.RequestBlob()
            mess.ParseFromString(message)
            self.Log.debug("message: RequestBlob : %s", mess)
            
        elif type == PYMUMBLE_MSG_TYPES_SERVERCONFIG:
            mess = mumble_pb2.ServerConfig()
            mess.ParseFromString(message)
            self.Log.debug("message: ServerConfig : %s", mess)        

    def set_bandwidth(self, bandwidth):
        """set the total allowed outgoing bandwidth"""
        if self.server_max_bandwidth is not None and bandwidth > self.server_max_bandwidth:
            self.bandwidth = self.server_max_bandwidth
        else: 
            self.bandwidth = bandwidth
            
        self.sound_output.set_bandwidth(self.bandwidth)  # communicate the update to the outgoing audio manager
    
    def sound_received(self, message):
        """Manage a received sound message"""
#        from tools import toHex  # for debugging

        pos = 0
        
#        self.Log.debug("sound packet : " + toHex(message))  # for debugging
                
        (header, ) = struct.unpack("!B", message[pos])  # extract the header
        type = ( header & 0b11100000 ) >> 5
        target = header & 0b00011111
        pos += 1
        
        if type == PYMUMBLE_AUDIO_TYPE_PING:
            return
            
        session = tools.VarInt()  # decode session id
        pos += session.decode(message[pos:pos+10])
        
        sequence = tools.VarInt()  # decode sequence number
        pos += sequence.decode(message[pos:pos+10])
        
        self.Log.debug("audio packet received from %i, sequence %i, type:%i, target:%i, lenght:%i", session.value, sequence.value, type, target, len(message))
        
        terminator = False  # set to true if it's the last 10 ms audio frame for the packet (used with CELT codec)
        while ( pos < len(message)) and not terminator:  # get the audio frames one by one
            if type == PYMUMBLE_AUDIO_TYPE_OPUS:
                size = tools.VarInt()  # OPUS use varint for the frame length
                
                pos += size.decode(message[pos:pos+10])
                size = size.value
                
                if not (size & 0x2000):  # terminator is 0x2000 in the resulting int.
                    terminator = True    # should actually always be 0 as OPUS can use variable length audio frames
                
                size = size & 0x1fff  # isolate the size from the terminator
            else:
                (header, ) = struct.unpack("!B", message[pos])  # CELT length and terminator is encoded in a 1 byte int
                if not (header & 0b10000000):
                    terminator = True
                size = header & 0b01111111
                pos += 1
    
            self.Log.debug("Audio frame : time:%f, last:%s, size:%i, type:%i, target:%i, pos:%i",time.time(), str(terminator), size, type, target, pos-1)

            if size > 0 and self.receive_sound:  # if audio must be treated
                try:
                    newsound = self.users[session.value].sound.add(message[pos:pos+size],
                                                                   sequence.value,
                                                                   type,
                                                                   target)  # add the sound to the user's sound queue

                    self.callbacks(PYMUMBLE_CLBK_SOUNDRECEIVED, self.users[session.value], newsound)
            
                    self.Log.debug("Audio frame : time:%f last:%s, size:%i, uncompressed:%i, type:%i, target:%i",time.time(), str(terminator), size, newsound.size, type, target)
                except CodecNotSupportedError as msg:
                    print msg
                except KeyError:  # sound received after user removed
                    pass

                sequence.value += int(round(newsound.duration / 1000 * 10))  # add 1 sequence per 10ms of audio 

#            if len(message) - pos < size:
#                raise InvalidFormatError("Invalid audio frame size")
            
            pos += size  # go further in the packet, after the audio frame
            
#TODO: get position info
            
    def set_application_string(self, string):
        """Set the application name, that can be viewed by other clients on the server"""
        self.application = string

    def set_loop_rate(self, rate):
        """set the current main loop rate (pause per iteration)"""
        self.loop_rate = rate
        
    def get_loop_rate(self):
        """get the current main loop rate (pause per iteration)"""
        return(self.loop_rate)

    def set_receive_sound(self, value):
        """Enable or disable the management of incoming sounds"""
        if value:
            self.receive_sound = True
        else:
            self.receive_sound = False

    def is_ready(self):
        """Wait for the connection to be fully completed.  To be used in the main thread"""
        self.ready_lock.acquire()
        self.ready_lock.release()
        
    def execute_command(self, cmd, blocking=True):
        """Create a command to be sent to the server.  To be userd in the main thread"""
        self.is_ready()
        
        lock = self.commands.new_cmd(cmd)
        if blocking and self.mumble_thread is not threading.current_thread():
            lock.acquire()
            lock.release()

        return lock
#TODO: manage a timeout for blocking commands.  Currently, no command actually waits for the server to execute
#      The result of these commands should actually be checked against incoming server updates
        
    def treat_command(self, cmd):
        """Send the awaiting commands to the server.  Used in the pymumble thread."""
        if cmd.cmd == PYMUMBLE_CMD_MOVE:
            userstate = mumble_pb2.UserState()
            userstate.session = cmd.parameters["session"]
            userstate.channel_id = cmd.parameters["channel_id"]
            self.Log.debug("Moving to channel")
            self.send_message(PYMUMBLE_MSG_TYPES_USERSTATE, userstate)
            cmd.response = True
            self.commands.answer(cmd)
        elif cmd.cmd == PYMUMBLE_CMD_MODUSERSTATE:
            userstate = mumble_pb2.UserState()
            userstate.session = cmd.parameters["session"]
            
            if "mute" in cmd.parameters:
                userstate.mute = cmd.parameters["mute"]
            if "self_mute" in cmd.parameters:
                userstate.self_mute = cmd.parameters["self_mute"]
            if "deaf" in cmd.parameters:
                userstate.deaf = cmd.parameters["deaf"]
            if "self_deaf" in cmd.parameters:
                userstate.self_deaf = cmd.parameters["self_deaf"]
            if "suppress" in cmd.parameters:
                userstate.suppress = cmd.parameters["suppress"]
            if "recording" in cmd.parameters:
                userstate.recording = cmd.parameters["recording"]
            if "comment" in cmd.parameters:
                userstate.comment = cmd.parameters["comment"]
            if "texture" in cmd.parameters:
                userstate.texture = cmd.parameters["texture"]
                
            self.send_message(PYMUMBLE_MSG_TYPES_USERSTATE, userstate)
            cmd.response = True
            self.commands.answer(cmd)

            
            
            
            
            
