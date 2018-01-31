import wave, struct, math

taplengthinseconds = 8.0 / 985248.0
samplerate = 44100.0
duration = 1.0
frequency = 440.0
checksum = 0

shortpulse = 0x30
mediumpulse = 0x42
longpulse = 0x56

wavef = 0
invert = 0

def openwavefile(name):
 global wavef;
 wavef = wave.open(name, 'w')
 wavef.setnchannels(1)
 wavef.setsampwidth(2)
 wavef.setframerate(44100.0)

def closewavefile():
 global wavef;
 wavef.writeframes('')
 wavef.close()

def addcycle( lengthinseconds ):
 global wavef
 global invert
 numberofsteps = int(samplerate * lengthinseconds)
 for i in range(numberofsteps):
  value = int(32767.0 * math.sin(float(i) / float(numberofsteps) * 2.0 * math.pi))
  if invert:
   value = -value
  data = struct.pack('<h', value)
  wavef.writeframesraw(data)

def addtapcycle( tapvalue ):
 addcycle(tapvalue * taplengthinseconds)

def addbit(value):
 if (value == 0):
  addtapcycle(shortpulse)
  addtapcycle(mediumpulse)
 else:
  addtapcycle(mediumpulse)
  addtapcycle(shortpulse)

def adddatamarker(moretofollow):
 if moretofollow:
  addtapcycle(longpulse)
  addtapcycle(mediumpulse)
 else:
  addtapcycle(longpulse)
  addtapcycle(shortpulse)

def resetchecksum():
 global checksum
 checksum = 0

def computechecksum():
 global checksum
 return checksum

def addbyteframe(value, moretofollow):
 global checksum
 checkbit = 1
 for i in range(8):
  if (value & (1 << i)) != 0:
   bit = 1
  else:
   bit = 0
  addbit(bit) 
  checkbit ^= bit
 addbit(checkbit)
 adddatamarker(moretofollow)
 checksum ^= value
 
def addleader(type):
 if (type == 0):
  numberofpulses = 0x6a00
 elif (type == 1):
  numberofpulses = 0x1a00
 else:
  numberofpulses = 0x4f
 for i in range(numberofpulses):
  addtapcycle( shortpulse )

def addsyncchain(repeated):
 if repeated:
  value = 0x09
 else:
  value = 0x89
 count = 9
 while (count > 0):
  addbyteframe(value, True)
  value-=1
  count-=1

def adddata(buffer, length):
 for i in range(length):
  addbyteframe(buffer[i], True)

def addheader(repeated, type, startaddress, endaddress, filenamebytes):
  if (repeated):
   addleader(2)
  else:
   addleader(0)
  adddatamarker(True)
  addsyncchain(repeated)
  resetchecksum()
  if type != 2:
   addbyteframe(type, True)
   addbyteframe(startaddress & 0x00ff, True)
   addbyteframe((startaddress & 0xff00) >> 8, True)
   addbyteframe(endaddress & 0x00ff, True)
   addbyteframe((endaddress & 0xff00) >> 8, True)
   adddata(filenamebytes, 16)
  for i in range(171):
   addbyteframe(0x20, True)
  addbyteframe(computechecksum(), False)

def addfile(filebytes, length):
 repeated = False
 for i in range(2):
  if (not repeated):
   addleader(1)
  else:
   addleader(2)
  adddatamarker(True)
  addsyncchain(repeated)
  resetchecksum()
  adddata(filebytes, length)
  addbyteframe(computechecksum(), False)
  repeated = True
 addleader(1)

openwavefile('test.wav')

filename = [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16]
filedata = [65, 66, 67, 68]

addheader(False, 3, 1024, 1100, filename)
addheader(True, 3, 1024, 1100, filename)
addfile(filedata, 4)

closewavefile()

