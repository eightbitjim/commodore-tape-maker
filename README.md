# commodore-tape-maker
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

## Example:
Convert a single PRG file called `game.prg` to a wav file (filename defaults to `out.wav`), with a Commodore filename of `game`. Automatically detects whether it is a BASIC program or not:

`python tap2wavPY.py game.prg game`

Same as above but invert the output signal, which often fixes problems loading into a real Commodore:

`python tap2wavPY.py -invert game.prg game`

Convert two PRG files to a single WAV file called `files.wav`. Force output to be a sine wave:

`python tap2wavPY.py -sine loader.prg loader game.prg game`

