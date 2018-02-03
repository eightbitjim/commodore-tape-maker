# MIT License
#
# Copyright (c) 2018 eightbitjim
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import wave, struct, math, sys

class outputsoundfile:
 def __init__(self, name, options):
  self.name = name
  self.options = options
  self.samplerate = 44100.0
  self.wavef = 0
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
   if self.options.sinewave:
    value = int(32767.0 * math.sin(float(i) / float(numberofsteps) * 2.0 * math.pi))
   else:
    if i < numberofsteps / 2:
     value = 32767
    else:
     value = -32767
   if self.options.invertwaveform:
    value = -value
   data = struct.pack('<h', value)
   self.wavef.writeframesraw(data)


class commodorefile:
 def __init__(self, filename, options):
  self.taplengthinseconds = 8.0 / 985248.0
  self.shortpulse = 0x30
  self.mediumpulse = 0x42
  self.longpulse = 0x56
  self.options = options
  self.checksum = 0
  self.data = []
  self.filenamedata = self.makefilename(filename)
  self.startaddress = 0
  self.endaddress = 0
  self.filetype = 3
  self.wavefile = 0

 def makefilename(self, filename):
  buffer = []
  filenamebuffersize = 0x10
  space = 0x20
  for i in range(filenamebuffersize):
   if len(filename) <= i:
    buffer.append(space)
   else:
    buffer.append(ord(filename[i].lower()))
  
  return buffer

 def setcontent(self, inputfile):
  self.data = inputfile.data
  self.startaddress = inputfile.startaddress
  self.endaddress = inputfile.startaddress + len(inputfile.data)
  if self.options.forcerelocatable:
   self.filetype = 3
  elif self.options.forcenonrelocatable:
   self.filetype = 1
  else:
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
 def __init__(self, filename, options):
  self.filename = filename
  self.options = options
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

class options:
 def __init__(self):
  self.invertwaveform = False
  self.sinewave = False
  self.forcerelocatable = False
  self.forcenonrelocatable = False
 
class commandline:
 def __init__(self, arguments):
  self.arguments = arguments
  self.options = options()
  self.currentargument = 0
  self.inputfiles = []
  self.error = False
  self.scriptname = self.nextargument()
  self.outfile = 'out.wav'
  self.parse()
    
 def addfile(self, filename, commodorefilename):
  self.inputfiles.append((filename, commodorefilename))

 def nextargument(self):
  if self.currentargument >= len(self.arguments):
   return None
  else:
   arg = self.arguments[self.currentargument]  
   self.currentargument += 1
   return arg

 def parseswitch(self, switch):
  switch = switch.lower()
  if switch == '-invert':
   print 'Inverting waveform'
   self.options.invertwaveform = True
  elif switch == '-sine':
   print 'Sine wave output'
   self.options.sinewave = True
  elif switch == '-square':
   print 'Square wave output'
   self.options.sinewave = False
  elif switch.startswith('-output='):
   self.outfile = switch[8::]
   print 'Output file ', self.outfile
  elif switch == '-basic':
   print 'Forcing relocatable (BASIC) file type'
   self.options.forcerelocatable = True   
  elif switch == '-data':
   print 'Forcing non-relocatable (machine code / data) file type'
   self.options.forcenonrelocatable = True   
  else:
   print 'Unknown switch ', switch
   self.error = True  
    
 def parsefilename(self, name):
  commodorename = self.nextargument()
  if commodorename == None:
   print 'Missing commodore filename for ',name
   self.error = True
  else:
   self.inputfiles.append((name, commodorename))
 
 def parse(self):
  switches = True
  while not self.error:
   arg = self.nextargument()
   if arg == None:
    break
   if arg[0] != '-':
    switches = False
   if switches:
    self.parseswitch(arg)
   else:
    self.parsefilename(arg)

  if switches:
   print "No input files specified"
   self.error = True
   
  return self.error
     
   
#TODO:
# refactor command line parsing to cope with switches
# add switch for inverting waveform
# add switch for sine / square
# add C16/Plus 4 support
# add forced filetype

cl = commandline(sys.argv)
if cl.error:
   print 'Usage: python ', sys.argv[0], '[switches] <input prg filename> <c64 filename> [...]'
   print '       where [...] is zero or more additional pairs of filenames'
else:
  wavefile = outputsoundfile(cl.outfile, cl.options)
  for i in range(len(cl.inputfiles)):
   (infilename, c64name) = cl.inputfiles[i]
   prgfile = inputprgfile(infilename, cl.options)
   c64file = commodorefile(c64name, cl.options)
   c64file.setcontent(prgfile)
   c64file.generatesound(wavefile)
   wavefile.addsilence(2.0)
  wavefile.close()
