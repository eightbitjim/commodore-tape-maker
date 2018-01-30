import wave, struct, math

taplengthinseconds = 8.0 / 985248.0
samplerate = 44100.0
duration = 1.0
frequency = 440.0

shortpulse = 0x30
mediumpulse = 0x42
longpulse = 0x56

wavef = 0

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
 numberofsteps = int(samplerate * lengthinseconds)
 for i in range(numberofsteps):
  value = int(32767.0 * math.sin(float(i) / float(numberofsteps) * 2.0 * math.pi))
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

def addbyteframe(value, moretofollow):
 checkbit = 1
 for i in range(8):
  bit = value & (1 << i)
  addbit(bit) 
  checkbit ^= bit
 addbit(checkbit)
 adddatamarker(moretofollow)
 
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
 while (value > 0):
  addbyteframe(value, True)
  value-=1

def addheader(repeated):
  if (repeated):
   addleader(2)
  else:
   addleader(0)
  adddatamarker(True)
  addsyncchain(repeated)
  pass

def addfile():
 addleader(1)

openwavefile('test.wav')

addheader(False)
addfile()

closewavefile()

