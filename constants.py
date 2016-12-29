"""Python constants."""

STAGE2_SIZE = 0x300

"""
fake_free_chunk

2nd dword needs to be big enough, and it is
3rd, 4th dword are null so it looks like the list is empty
0x15D62F10:  0x15D62F48 ; no idea
0x15D62F14:  0x15D62F54 ; >= desired size
0x15D62F18:  0x00000000 ; prev
0x15D62F1C:  0x00000000 ; next
"""

"""
start/end1

we don't want the corrupted chunk to get added to the free
list when it's freed, so put fake size data in the header
so it doesn't get added.
"""

"""
sleep_gadget

.text:001B5A5C                 LDMFD           SP!, {R4-R6,LR}
.text:001B5A60                 B               sleep
"""

"""
gpu_flushcache_gadget

.text:002E2954                 STMFD           SP!, {R4-R6,LR}
.text:002E2958                 MOV             R4, R0 <- jump here
.text:002E295C                 LDR             R0, =dword_30CF2C
.text:002E2960                 MOV             R6, R1
.text:002E2964                 LDR             R5, [R0]
.text:002E2968                 BL              unknown_libname_289
.text:002E296C                 MOV             R3, R6
.text:002E2970                 MOV             R2, R4
.text:002E2974                 MOV             R1, R5
.text:002E2978                 LDMFD           SP!, {R4-R6,LR}
.text:002E297C                 B               sub_2E978C
"""

"""
gpu_enqueue_gadget

.text:002E96FC                 BL              gsp__GetInterruptReceiver
.text:002E9700                 ADD             R0, R0, #0x58
.text:002E9704                 ADD             R1, SP, #4
.text:002E9708                 BL              gsp__EnqueueGpuCommand
.text:002E970C                 ADD             SP, SP, #0x24
.text:002E9710                 LDMFD           SP!, {R4-R11,PC}
"""

constants = {
    "fake_free_chunk": {
        "usa": 0x15D62F10,
        "eur": 0x15D62F10,
        "jpn": 0x15D62F10,
        "kor": 0x15D69A94,
        },
    "heapctx": {
        "usa": 0x0039B560,
        "eur": 0x0039B580,
        "jpn": 0x0039B520,
        "kor": 0x003B4520,
        },
    "start": {
        "usa": 0x140018AF,
        "eur": 0x140018AF,
        "jpn": 0x140018AF,
        "kor": 0x140018AF,
        },
    "end1": {
        "usa": 0x14001920,
        "eur": 0x14001920,
        "jpn": 0x14001920,
        "kor": 0x14001920,
        },
    "sleep_gadget": {
        "usa": 0x001B5A5C,
        "eur": 0x002F11C0,
        "jpn": 0x002F0F28,
        "kor": 0x0012A6C8,
        },
    "gpu_flushcache_gadget": {
        "usa": 0x002E2958,
        "eur": 0x002E2AC8,
        "jpn": 0x002E2830,
        "kor": 0x0012B730,
        },
    "gpu_enqueue_gadget": {
        "usa": 0x002E96FC,
        "eur": 0x002E9428,
        "jpn": 0x002E95D4,
        "kor": 0x00131B0C,
        },
    "memcpy_gadget": {
        "usa": 0x0022DB1C,
        "eur": 0x0022DB1C,
        "jpn": 0x0022DB1C,
        "kor": 0x00228910,
        },
    "pop_r0_pc": {
        "usa": 0x002e6f80,
        "eur": 0x002E70F0,
        "jpn": 0x002E6E58,
        "kor": 0x0012FA94,
        },
    "pop_r1_pc": {
        "usa": 0x0022B6C8,
        "eur": 0x0022B6C8,
        "jpn": 0x0022B6C8,
        "kor": 0x002220E0,
        },
    "payload_stack_addr": {
        "usa": 0x15D630C8,
        "eur": 0x15D630C8,
        "jpn": 0x15D630C8,
        "kor": 0x15D69C38,
        },
    "stage2_code_va": {
        "usa": 0x002F5D00,
        "eur": 0x002F5D00,
        "jpn": 0x002F5D00,
        "kor": 0x002F5D00,
        },
    "pop_r2_thru_r6_pc": {
        "usa": 0x0021462C,
        "eur": 0x00108910,
        "jpn": 0x0021462C,
        "kor": 0x00148740,
        },
    "payload_heap_addr": {
        "usa": 0x14200000,
        "eur": 0x14200000,
        "jpn": 0x14200000,
        "kor": 0x14200000,
        }
}
