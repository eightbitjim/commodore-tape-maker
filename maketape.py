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

import math
import struct
import sys
import wave


class OutputSoundFile:
    def __init__(self, name, options):
        self.name = name
        self.options = options
        self.sample_rate = 44100.0
        self.wave_file = None
        self.open()

    def open(self):
        self.wave_file = wave.open(self.name, 'w')
        self.wave_file.setnchannels(1)
        self.wave_file.setsampwidth(2)
        self.wave_file.setframerate(self.sample_rate)

    def close(self):
        self.wave_file.writeframes('')
        self.wave_file.close()

    def add_silence(self, length_in_seconds):
        number_of_steps = int(self.sample_rate * length_in_seconds)
        for i in range(number_of_steps):
            value = 0
            data = struct.pack('<h', value)
            self.wave_file.writeframesraw(data)

    def add_cycle(self, length_in_seconds):
        number_of_steps = int(self.sample_rate * length_in_seconds)

        for i in range(number_of_steps):
            if self.options.sine_wave:
                value = 0 - int(32767.0 * math.sin(float(i) / float(number_of_steps) * 2.0 * math.pi))
            else:
                if i < number_of_steps / 2:
                    value = -32767
                else:
                    value = 32767
            if self.options.invert_waveform:
                value = -value
            data = struct.pack('<h', value)
            self.wave_file.writeframesraw(data)


class CommodoreFile:
    TAP_LENGTH_IN_SECONDS = 8.0 / 985248.0
    FILENAME_BUFFER_SIZE = 0x10
    FILE_TYPE_NONE = 0
    FILE_TYPE_RELOCATABLE = 1
    FILE_TYPE_SEQUENTIAL = 2
    FILE_TYPE_NON_RELOCATABLE = 3
    LEADER_TYPE_HEADER = 0
    LEADER_TYPE_CONTENT = 1
    LEADER_TYPE_REPEATED = 2
    NUMBER_OF_PADDING_BYTES = 171
    PADDING_CHARACTER = 0x20
    SHORT_PULSE = 0x30
    MEDIUM_PULSE = 0x42
    LONG_PULSE = 0x56

    def __init__(self, filename, options):
        self.options = options
        self.checksum = 0
        self.data = []
        self.filename_data = self.make_filename(filename)
        self.start_address = 0
        self.end_address = 0
        self.file_type = self.FILE_TYPE_NONE
        self.wave_file = None

    def make_filename(self, filename):
        filename_buffer = []
        space = 0x20
        for i in range(self.FILENAME_BUFFER_SIZE):
            if len(filename) <= i:
                filename_buffer.append(space)
            else:
                filename_buffer.append(ord(filename[i]))

        return filename_buffer

    def set_content(self, input_file):
        self.data = input_file.data
        self.start_address = input_file.start_address
        self.end_address = input_file.start_address + len(input_file.data)
        self.file_type = input_file.type

    def generate_sound(self, output_wave_file):
        self.wave_file = output_wave_file
        self.add_header(False)
        self.add_header(True)
        output_wave_file.add_silence(0.1)
        self.add_file()

    def add_tap_cycle(self, tap_value):
        self.wave_file.add_cycle(tap_value * self.TAP_LENGTH_IN_SECONDS)

    def add_bit(self, value):
        if value == 0:
            self.add_tap_cycle(self.SHORT_PULSE)
            self.add_tap_cycle(self.MEDIUM_PULSE)
        else:
            self.add_tap_cycle(self.MEDIUM_PULSE)
            self.add_tap_cycle(self.SHORT_PULSE)

    def add_data_marker(self, more_to_follow):
        if more_to_follow:
            self.add_tap_cycle(self.LONG_PULSE)
            self.add_tap_cycle(self.MEDIUM_PULSE)
        else:
            self.add_tap_cycle(self.LONG_PULSE)
            self.add_tap_cycle(self.SHORT_PULSE)

    def reset_checksum(self):
        self.checksum = 0

    def add_byte_frame(self, value, more_to_follow):
        check_bit = 1
        for i in range(8):
            if (value & (1 << i)) != 0:
                bit = 1
            else:
                bit = 0
            self.add_bit(bit)
            check_bit ^= bit

        self.add_bit(check_bit)
        self.add_data_marker(more_to_follow)
        self.checksum ^= value

    def add_leader(self, type):
        if type == self.LEADER_TYPE_HEADER:
            number_of_pulses = 0x6a00
        elif type == self.LEADER_TYPE_CONTENT:
            number_of_pulses = 0x1a00
        else:
            number_of_pulses = 0x4f

        for i in range(number_of_pulses):
            self.add_tap_cycle(self.SHORT_PULSE)

    def add_sync_chain(self, repeated):
        if repeated:
            value = 0x09
        else:
            value = 0x89

        count = 9
        while count > 0:
            self.add_byte_frame(value, True)
            value -= 1
            count -= 1

    def add_data(self):
        for i in range(len(self.data)):
            self.add_byte_frame(self.data[i], True)

    def add_filename(self):
        for i in range(len(self.filename_data)):
            self.add_byte_frame(self.filename_data[i], True)

    def add_header(self, repeated):
        if repeated:
            self.add_leader(self.LEADER_TYPE_REPEATED)
        else:
            self.add_leader(self.LEADER_TYPE_HEADER)

        self.add_data_marker(True)
        self.add_sync_chain(repeated)
        self.reset_checksum()

        self.add_byte_frame(self.file_type, True)
        self.add_byte_frame(self.start_address & 0x00ff, True)
        self.add_byte_frame((self.start_address & 0xff00) >> 8, True)
        self.add_byte_frame(self.end_address & 0x00ff, True)
        self.add_byte_frame((self.end_address & 0xff00) >> 8, True)
        self.add_filename()

        for i in range(self.NUMBER_OF_PADDING_BYTES):
            self.add_byte_frame(self.PADDING_CHARACTER, True)

        self.add_byte_frame(self.checksum, False)

    def add_file(self):
        repeated = False
        for i in range(2):
            if not repeated:
                self.add_leader(self.LEADER_TYPE_CONTENT)
            else:
                self.add_leader(self.LEADER_TYPE_REPEATED)

            self.add_data_marker(True)
            self.add_sync_chain(repeated)
            self.reset_checksum()
            self.add_data()

            self.add_byte_frame(self.checksum, False)
            repeated = True

        self.add_leader(1)


class InputPRGFile:
    TYPE_NONE = 0
    TYPE_RELOCATABLE = 1
    TYPE_SEQUENTIAL = 2
    TYPE_NON_RELOCATABLE = 3
    TYPE_STRING = ['none', 'relocatable (BASIC) program', 'sequential (SEQ) file',
                   'non-relacatable (machine code / data)']

    def __init__(self, filename, options):
        self.filename = filename
        self.options = options
        self.start_address = 0
        self.type = 0
        self.data = []
        self.read()
        print 'Filename: ', filename
        print 'Length: ', len(self.data)
        print 'Start address: ', self.start_address
        print 'End address: ', self.start_address + len(self.data)
        print 'Type: ', self.TYPE_STRING[self.type]

    def read(self):
        f = open(self.filename, 'rb')
        try:
            self.start_address = ord(f.read(1)[0]) + 0x100 * ord(f.read(1)[0])
            byte = f.read(1)
            while byte != '':
                self.data.append(ord(byte[0]))
                byte = f.read(1)
        finally:
            f.close()

        if self.options.force_non_relocatable:
            self.type = 3
        elif self.options.force_relocatable:
            self.type = 1
        else:
            self.type = 3
            if self.start_address == 4097 or self.start_address == 2049:
                self.type = 1


class Options:
    def __init__(self):
        self.invert_waveform = False
        self.sine_wave = True
        self.force_relocatable = False
        self.force_non_relocatable = False


class CommandLine:
    def __init__(self, arguments):
        self.arguments = arguments
        self.options = Options()
        self.current_argument = 0
        self.input_files = []
        self.error = False
        self.script_name = self.next_argument()
        self.out_file = 'out.wav'
        self.parse()

    def add_file(self, input_filename, commodore_filename):
        self.input_files.append((input_filename, commodore_filename))

    def next_argument(self):
        if self.current_argument >= len(self.arguments):
            return None
        else:
            arg = self.arguments[self.current_argument]
            self.current_argument += 1
            return arg

    def parse_switch(self, switch):
        switch = switch.lower()
        if switch == '-invert':
            print 'Inverting waveform'
            self.options.invert_waveform = True
        elif switch == '-sine':
            print 'Sine wave output'
            self.options.sine_wave = True
        elif switch == '-square':
            print 'Square wave output'
            self.options.sine_wave = False
        elif switch.startswith('-output='):
            self.out_file = switch[8::]
            print 'Output file ', self.out_file
        elif switch == '-basic':
            print 'Forcing relocatable (BASIC) file type'
            self.options.force_relocatable = True
        elif switch == '-data':
            print 'Forcing non-relocatable (machine code / data) file type'
            self.options.force_non_relocatable = True
        else:
            print 'Unknown switch ', switch
            self.error = True

    def parse_filename(self, name):
        commodore_filename = self.next_argument().upper()
        if commodore_filename is None:
            print 'Missing commodore filename for ', name
            self.error = True
        else:
            self.input_files.append((name, commodore_filename))

    def parse(self):
        switches = True
        while not self.error:
            arg = self.next_argument()
            if arg is None:
                break
            if arg[0] != '-':
                switches = False
            if switches:
                self.parse_switch(arg)
            else:
                self.parse_filename(arg)

        if switches:
            print "No input files specified"
            self.error = True
        return self.error


cl = CommandLine(sys.argv)
if cl.error:
    print 'Usage: python ', sys.argv[0], '[switches] <input prg filename> <c64 filename> [...]'
    print '       where [...] is zero or more additional pairs of filenames'
    print 'switches:'
    print ' -invert : invert the output waveform'
    print "           (this often fixes the problem if you can't load the file on a real commodore)"
    print ' -sine   : force sine wave output (the default)'
    print ' -square : force square wave output'
    print ' -basic  : force all files to be relocatable (BASIC) program files'
    print ' -data   : force all files to be non-relocatable (non-BASIC) files'
    print '           (the default is to automatically detect the file type based on load address)'
    print ' -output=<filename> : specifies the name of the output WAV file. Default is out.wav'
else:
    wave_file = OutputSoundFile(cl.out_file, cl.options)
    for i in range(len(cl.input_files)):
        (in_filename, c64name) = cl.input_files[i]
        prg_file = InputPRGFile(in_filename, cl.options)
        c64_file = CommodoreFile(c64name, cl.options)
        c64_file.set_content(prg_file)
        c64_file.generate_sound(wave_file)
        wave_file.add_silence(2.0)
    wave_file.close()
