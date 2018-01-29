import wave, struct, math

taplengthinseconds = 8.0 / 985248.0
samplerate = 44100.0
duration = 1.0
frequency = 440.0

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

openwavefile('test.wav')
addcycle(0.01)
closewavefile()

