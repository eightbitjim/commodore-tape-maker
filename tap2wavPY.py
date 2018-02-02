import wave, struct, math, sys

class outputsoundfile:
 def __init__(self, name):
  self.name = name
  self.samplerate = 44100.0
  self.wavef = 0
  self.invert = 0
  self.open()

 def open(self):
  global wavef;
  self.wavef = wave.open(self.name, 'w')
  self.wavef.setnchannels(1)
  self.wavef.setsampwidth(2)
  self.wavef.setframerate(self.samplerate)

 def close(self):
  self.wavef.writeframes('')
  self.wavef.close()

 def addsilence(self, lengthinseconds):
  numberofsteps = int(self.samplerate * lengthinseconds)
  for i in range(numberofsteps):
   value = 0
   data = struct.pack('<h', value)
   self.wavef.writeframesraw(data)
   
 def addcycle(self, lengthinseconds ):
  numberofsteps = int(self.samplerate * lengthinseconds)
  
  for i in range(numberofsteps):
   value = int(32767.0 * math.sin(float(i) / float(numberofsteps) * 2.0 * math.pi))
   if self.invert:
    value = -value
   data = struct.pack('<h', value)
   self.wavef.writeframesraw(data)


class commodorefile:
 def __init__(self, filename):
  self.taplengthinseconds = 8.0 / 985248.0
  self.shortpulse = 0x30
  self.mediumpulse = 0x42
  self.longpulse = 0x56
  self.checksum = 0
  self.data = []
  self.filenamedata = self.makefilename(filename)
  self.startaddress = 0
  self.endaddress = 0
  self.filetype = 3
  self.wavefile = 0

 def makefilename(self, filename):
  return [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16]

 def setcontent(self, inputfile):
  self.data = inputfile.data
  self.startaddress = inputfile.startaddress
  self.endaddress = inputfile.startaddress + len(inputfile.data)
  self.filetype = inputfile.type

 def generatesound(self, outputwavefile):
  self.wavefile = outputwavefile
  self.addheader(False)
  self.addheader(True)
  outputwavefile.addsilence(0.1)
  self.addfile()

 def addtapcycle(self, tapvalue ):
  wavefile.addcycle(tapvalue * self.taplengthinseconds)
 
 def addbit(self, value):
  if (value == 0):
   self.addtapcycle(self.shortpulse)
   self.addtapcycle(self.mediumpulse)
  else:
   self.addtapcycle(self.mediumpulse)
   self.addtapcycle(self.shortpulse)

 def adddatamarker(self, moretofollow):
  if moretofollow:
   self.addtapcycle(self.longpulse)
   self.addtapcycle(self.mediumpulse)
  else:
   self.addtapcycle(self.longpulse)
   self.addtapcycle(self.shortpulse)

 def resetchecksum(self):
  self.checksum = 0
 
 def addbyteframe(self, value, moretofollow):
  checkbit = 1
  for i in range(8):
   if (value & (1 << i)) != 0:
    bit = 1
   else:
    bit = 0
   self.addbit(bit) 
   checkbit ^= bit
   
  self.addbit(checkbit)
  self.adddatamarker(moretofollow)
  self.checksum ^= value
 
 def addleader(self, type):
  if (type == 0):
   numberofpulses = 0x6a00
  elif (type == 1):
   numberofpulses = 0x1a00
  else:
   numberofpulses = 0x4f
   
  for i in range(numberofpulses):
   self.addtapcycle( self.shortpulse )

 def addsyncchain(self, repeated):
  if repeated:
   value = 0x09
  else:
   value = 0x89

  count = 9
  while (count > 0):
   self.addbyteframe(value, True)
   value-=1
   count-=1 
 
 def adddata(self):
  for i in range(len(self.data)):
   self.addbyteframe(self.data[i], True)

 def addfilename(self):
  for i in range(len(self.filenamedata)):
   self.addbyteframe(self.filenamedata[i], True)
  
 def addheader(self, repeated):
   if (repeated):
    self.addleader(2)
   else:
    self.addleader(0)
    
   self.adddatamarker(True)
   self.addsyncchain(repeated)
   self.resetchecksum()
   
   self.addbyteframe(self.filetype, True)
   self.addbyteframe(self.startaddress & 0x00ff, True)
   self.addbyteframe((self.startaddress & 0xff00) >> 8, True)
   self.addbyteframe(self.endaddress & 0x00ff, True)
   self.addbyteframe((self.endaddress & 0xff00) >> 8, True)
   self.addfilename()
   
   for i in range(171):
    self.addbyteframe(0x20, True)
    
   self.addbyteframe(self.checksum, False)

 def addfile(self):
  repeated = False
  for i in range(2):
   if (not repeated):
    self.addleader(1)
   else:
    self.addleader(2)
    
   self.adddatamarker(True)
   self.addsyncchain(repeated)
   self.resetchecksum()
   self.adddata()
   
   self.addbyteframe(self.checksum, False)
   repeated = True
   
  self.addleader(1) 
 
 
class inputprgfile:
 def __init__(self, filename):
  self.filename = filename
  self.read()
  self.typestring = ['none', 'relocatable (BASIC) program', 'sequential (SEQ) file', 'non-relacatable (machine code / data)']
  print 'Filename: ', filename
  print 'Length: ', len(self.data)
  print 'Start address: ', self.startaddress
  print 'Type: ', self.typestring[self.type]
   
 def read(self):
  self.data = []
  f = open(self.filename, 'rb')
  try:
   self.startaddress = ord(f.read(1)[0]) + 0x100 * ord(f.read(1)[0])
   byte = f.read(1)
   while byte != '':
    self.data.append(ord(byte[0]))
    byte = f.read(1)
  finally:
   f.close()

  self.type = 3   
  if self.startaddress == 4097 or self.startaddress == 2049:
   self.type = 1
  
error = False

if len(sys.argv) < 2:
 error = True
else:
 numberofpairs = len(sys.argv) - 1
 if ((numberofpairs % 2) != 0):
  print "Error. Must specify pairs of filenames."
  error = True
 
 numberofpairs /= 2
 
 if (not error):
  outfilename = 'out.wav'
  wavefile = outputsoundfile(outfilename)
  for i in range(numberofpairs):
   infilename = sys.argv[1 + i * 2]
   c64name = sys.argv[2 + i * 2]
   prgfile = inputprgfile(infilename)
   c64file = commodorefile(c64name)
   c64file.setcontent(prgfile)
   c64file.generatesound(wavefile)
   wavefile.addsilence(2.0)
  wavefile.close()

if error:
 print 'Usage: python ', sys.argv[0], ' <input prg filename> <c64 filename> [...]'
 print '       where [...] is zero or more additional pairs of filenames'
