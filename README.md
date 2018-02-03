# c64-tools
A python script to generate Commodore 64-compatible audio tape files from `PRG` files. The format is also compatible with the Commodore Vic 20 and PET.

Input files are `PRG`, output are mono uncompressed `WAV`.

# Command line:
The following assumes that you have python installed and can run it from the command line.

`python tap2wavPY.py [switches] <input PRG> <commodore filename> [<input PRG><commodore filename>] ...`

* `<input PRG>` is a `PRG` file to convert to audio. The first two bytes of the file must specify the load address in the
Commodore-computer's memory. The remaining bytes of the file are assumed to be data. There is no checksum or any other structure to the file.
* `<commodore filename>` is the filename that the Commodore computer will see and display in `SEARCHING / FOUND xxx`.

You can optionally specify more than one input file / filename pair, in which case all of the files will be appended into a single output
`WAV` file, with a second of silence between each.

## Switches:
* `-invert`: invert the output waveform (this often fixes the problem if you can't load the file on a real commodore)
* `-sine`: force sine wave output
* `-square`: force square wave output (the default)
* `-basic`: force all files to be non-relocatable (BASIC) program files
* `-data`: force all files to be relocatable (non-BASIC) files (the default is to automatically detect the file type based on load address) 
* `-output=<filename>`: specifies the name of the output WAV file. Default is `out.wav`
