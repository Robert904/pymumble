API
===
## main Mumble object 
> class Mumble(host, port, user, password, client_certif=None, reconnect=False, debug=False)
it should be quite straightforward.  debug=True will generate a LOT of stdout messages...  otherwise it should be silent in normal conditions
reconnect should allow the library to reconnect automatically if the server disconnect it
  
> Mumble.start()
Start the library thread and the connection process

> Mumble.is_ready()
Block until the connection process is conluded

> Mumble.set_bandwidth(int)
Set (in bit per seconds) the allowed total outgoing bandwidth of the library.  Can be limited by the server

> Mumble.set_application_string(string)
Set the application name that will be sent to the server.  Must by done before the start()

> Mumble.set_loop_rate(float)
Set in second how long the library will wait for an incoming message, which slowdown the loop.
Must be small enough for the audio traetment you need, but if too small it will consume too much CPU
0.01 is the default and seems to be small enough to send audio in 20ms packets.
For application that just receive sound, bigger should be enough (like 0.05)

> Mumble.get_loop_rate()
return the current loop_rate

> Mumble.set_receive_sound(bool)
By default, incoming sound is not treated.  If you plan to use the incoming audio, you must set this to True,
but then you have to get the audio out of the library regularly otherwise it will simply takes memory...

## Callbacks object (accessible through Mumble.callbacks)
Manage the different available callbacks.
It is basically a dict of the available callbakcs and the methods to manage them.

Callback names are in pymumble.constants module, starting with "PYMUMBLE_CLBK_"
- PYMUMBLE_CLBK_CONNECTED: Connection succeeded
- PYMUMBLE_CLBK_CHANNELCREATED: send the created channel object as parameter
- PYMUMBLE_CLBK_CHANNELUPDATED: send the updated channel object and a dict with all the modified fields as parameter
- PYMUMBLE_CLBK_CHANNELREMOVED: send the removed channel object as parameter
- PYMUMBLE_CLBK_USERCREATED: send the added user object as parameter
- PYMUMBLE_CLBK_USERUPDATED: send the updated user object and a dict with all the modified fields as parameter
- PYMUMBLE_CLBK_USERREMOVED: send the removed user object and the mumble message as parameter
- PYMUMBLE_CLBK_SOUNDRECEIVED: send the user object that received the sound and the SoundChunk object itself
- PYMUMBLE_CLBK_TEXTMESSAGERECEIVED: Send the received message

!!! Callbacks are executed within the library looping thread.  Keep it's work short or you could have jitter issues !!!

> Mumble.callbacks.set_callback(callback, function)
Assign a function to a callback (replace the previous ones if any)

> Mumble.callbacks.add_callback(callback, function)
Assign an additionnal function to a callback

> Mumble.callbacks.get_callback(callback)
Return a list of functions assign to this callback or None

> Mumble.callbacks.remove_callback(callback, function)
Remove the specified function from the ones assign to this callback

> Mumble.callbacks.reset_callback(callback)
Remove all defined callback functions for this callback

> Mumble.callbacks.get_callbacks_list()
Return the list of all the available callbacks.  Better use the constants though


## Users object (accessible through Mumble.users)
Store the users connected on the server.  For the application, it is basically only interesting as a dict of User objects,
which contain the actual infomations

> Mumble.users[int]
where int is the session number on the server.  It point to the specific User object for this session

> Mumble.users.count()
return the number of connected users on the server

> Mumble.users.myself_session
Contain the session number of the pymumble connection itself

> Mumble.users.myself
is a shortcut to Mumble.users[Mumble.users.myself_session], poiting to the User object of the current connection


## User object (accessible through Mumble.users[session] or Mumble.users.myself
Contain the users informations and method to act on them.
User also contain an instance of the SoundQueue object, containing the audio received from this user

> User.sound
SoundQueue instance for this user

> User.get_property()
Return the value of the property.

> User.mute()
> User.unmute()

> User.deafen()
> User.undeafen()

> User.suppress()
> User.unsuppress()

> User.recording()
> User.unrecorfing()

> User.comment(string)
Set the comment for this user

> user.texture(texture)
Set the image for this user (must be a format recognized by the mumble clients.  PNG seems to work, I had issues with SVG)


## SoundQueue object (accessible through User.sound)
Contains the audio received from a specific user.
Take care of the decoding and keep track on the timing of the reception

> User.sound.set_receive_sound(bool)
Allow to stop treating incoming audio for a specific user if False.  True by default.

> User.sounf.is_sound()
Return True if sound if present in this SoudQueue

> User.sound.get_sound(duration=None)
Return a SoundChunk object containing the audio received in one packet coming from the server, and discard it from the list.
If duration (in sec) is specified and smaller than the size of the next available audio, the split is taken care of.
DO NOT USE A NON 10ms MULTIPLE AS IT IS THE BASIC UNIT IN MUMBLE

> User.sound.first_sound()
Return the a SoundChunk object (the next one) but do not discard it.
Useful to check it's timing without actually treat it yet


## SoundChunk object (received from User.sound)
It contains a sound unit, as received from the server.
It as several properties
> SoundChunk.pcm
the PCM buffer for this sound, in 16 bits signed mono little-endian 48000Hz format

> SoundChunk.timestamp
Time when the packet was received

> SoundChunk.time
Time calculated based on mumble sequences (better to reconstruct the stream)

> SoundChunk.sequence
Mumble sequence for the packet

> SoundChunk.size
Size of the PCM in bytes

> SoundChunk.duration
length of the PCM in secs

> SoundChunk.type
Mumble type for the chunk (coded used)

> SoundChunk.target
Target of the packet, as sent by the server 


## Channels object (accessible through Mumble.channels)
Contains the channels known on the server.  Allow to list and find them.
It is again a dict by channel ids (root=0) containing all the Channel objects

> Mumble.channels.find_by_tree(iterable)
Search, starting from the root for every element a subchannel with the same name.
Return the channel object or raise a UnknownChannelError exception

> Mumble.channels.get_childs(channel_id)
Return a list of all the childs objects for a channel id

> Mumble.channels.get_descendants(channel_id)
Return a (nested) list of the channels above this id

> Mumble.get_tree(channel_id)
Return a nested list of the channel objects above this id

> Mumble.find_by_name(name)
Return the first channel object matching the name


## Channel object (accessible through Mumble.channels[channel_id])
Contain the properties of the specific channel.
Allow to move a user into it

> Channel.get_property(name)
Return the property value for this channel

> Channel.move_in(session=None)
Move (or try to) a user's session into the channel.
If no session specified, try to move the library application itself


## SoundOutput object (accessible through Mumble.sound_output)
Takes care of encoding, packetizing and sending the audio to the server

> Mumble.sound_output.set_audio_per_packet(float)
Set the duration of one packet of audio in secs.  Typically 0.02 or 0.04. Max is 0.12 (codec limitations)

> Mumble.sound_output.get_audio_per_packet()
Return the current length of an audio packet in secs

> Mumble.sound_output.add_sound(string)
Add PCM sound (16 bites mono 48000Hz little-endian encoded) to the outgoing queue

> Mumble.sound_output.get_buffer_size()
Return in secs the size of the unsent audio buffer.  Usefull to transfer audio to the library at a regular pace







