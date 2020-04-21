# Soundhax

A heap overflow in tag processing leads to code execution when a specially-
crafted m4a file is loaded by Nintendo 3DS Sound.

This bug is particularly good, because as far as I can tell it is the first
ever homebrew exploit that is free, offline, and works on every version
of the firmware for which the sound app is available.

## Regions and Versions

| Version | N3DS/N2DS | O3DS/2DS |
| --- | --- | --- |
| US 2.1-11.3 | ✓ | ✓ |
| JPN 2.1-11.3 | ✓ | ✓ |
| EUR 2.1-11.3 | ✓ | ✓ |
| KOR 4.0-11.3 | ✓ | ✓ |
| CHN 4.0-11.3 | ✗ | ✗ |
| TWN 4.1-11.3 | ✗ | ✗ |

If your box is checked, then put [otherapp.bin](https://smealum.github.io/3ds/#otherapp) on the root of your SD card along with soundhax.m4a and launch the song from the sound player.

It can be used along [pre9otherapp](https://github.com/hax0kartik/pre9otherapp) to launch an arm9 payload from the SD card on pre 9.0 firms (2.1 - 9.2).

## Status for KOR/CHN/TWN

| Status | KOR | CHN | TWN |
| --- | --- | --- | --- |
| bug confirmed | ✓ | ✓ | ✗ |
| sound constants | ✓ | ✓ | ✗ |
| stage2 payload constants | ✓ | ✗ | ✗ |

## Installation
1. Download the relevant soundhax-region-console-firmware.m4a file for your device.
2. Save the soundhax song file and copy to the root of your SD.
3. Download the [otherapp payload](https://smealum.github.io/3ds/) for your 3DS version, rename it to `otherapp.bin`, and copy it to the root of the SD card.
4. Download the [Homebrew Menu](https://github.com/fincs/new-hbmenu/releases/latest) and place `boot.3dsx` in the root of the SD card (if it is not there already).
5. Insert the SD card into the 3DS and start Nintendo 3DS Sound.
6. Locate your new song and play it to start the Homebrew Menu!

Fixing the annoying bird: Click through all of the bird tips then close the app normally. When you exploit it it doesn't save the fact that you've opened the app before, so closing and reopening normally seems to fix this.

## Build
Install [Python 2.7](https://python.org) and [devkitARM](https://devkitpro.org/wiki/Getting_Started).

Then run `python exp.py <usa/eur/jpn/kor> <new/old> <v21and22/v3xand4x/post5>` to generate `soundhax-*.m4a`.

## Writeup

### The Bug
3DS Sound mallocs a buffer of 256 bytes to hold the name of song as described
in its mp4 atom tags. This is sensible since it's the maximum allowed size according
to the spec. When parsing an ascii title, `strncpy(dst, src, 256)` is used, which
is safe and correct. However, because unicode strings contain null bytes, rather
than using a unicode `strncpy` variant, the application simply `memcpy`s the name
bytes onto the heap using the user provided size, which can be arbitrarily large.

### Exploit
I overflow my data onto the next heap chunk, which lets me fully control the
malloc header of that chunk, which happens to be allocated at the time of the overflow.
When that chunk is freed, a heap unlink is performed, which allows me to do
an arbitrary write. This means I can write a dword to the stack and control
PC. Unfortunately, there aren't any usable gadgets (trust me, I looked), so I
had to use a more advanced technique to exploit the bug. I used the
arbitrary write to overwrite the free list header with a stack address,
while setting the start and end fields of the chunk being freed to cause the
block to appear undersized, thus causing it to not be added to the free list
and so the stack address I just wrote is used on the next malloc. Because malloc
jumps through the free list looking for a suitable block, I had to find a stack
address at which there appears to be a valid heap chunk header with a large enough
size for the requested allocation and null pointers for the next and prev entries
in the list, so that my stack chunk is chosen as the 'best' one. Once all of
these conditions are met, the next malloc returns the stack address as the
'heap' location to write my next tag data, which lets me turn the arbitrary
write primitive into ROP. From there I use the gspwn GPU exploit to write
my stage2 shellcode over the text section of the sound process, before finally
jumping to it.

In summary, the process looks like this:

heap overflow -> arbitrary write to free list -> stack overflow -> gspwn -> code execution

## Thanks
Subv and Citra authors - for help emulating sound, this was invaluable

plutoo   - stage 2 shellcode

yellows8 - help with gpu address translation for gspwn, initial JPN support, finished KOR support

smea     - homebrew launcher

d3m3vilurr - EUR, JPN, partial KOR support

TuxSH - O3DS offset

Konng - Testing EUR payloads

\#cakey - advice and support

PPP - teaching me everything I know

geohot, comex, j00ru, loki, project zero - inspiring me to pursue bug hunting
