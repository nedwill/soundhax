/* stage2 constants for system versions v2.1 and v2.2 */

#if defined(USA)

#define FS_OPEN_FILE 0x0022929C
#define GSP_GET_HANDLE 0x0021C960
#define GSP_GET_INTERRUPTRECEIVER 0x001C805C
#define GSP_ENQUEUE_CMD 0x001C7BF4

#define FS_READ_FILE 0x002C41F4
#define GSP_GX_CMD4 0x002E9380
#define GSP_FLUSH_DATA_CACHE 0x002E2940

#define SRV_SESSIONHANDLE 0x00374258
#define SRV_SEMAPHORE 0x00374248

#define THREAD8_EVENT_HANDLE 0x003C1308
#define THREAD8_OBJ 0x003C2658

#elif defined(EUR)

#define FS_OPEN_FILE 0x0022929C
#define GSP_GET_HANDLE 0x0021C960
#define GSP_GET_INTERRUPTRECEIVER 0x001C805C
#define GSP_ENQUEUE_CMD 0x001C7BF4

#define FS_READ_FILE 0x002C4364
#define GSP_GX_CMD4 0x002E94F0
#define GSP_FLUSH_DATA_CACHE 0x002E2AB0

#define SRV_SESSIONHANDLE 0x00374258
#define SRV_SEMAPHORE 0x00374248

#define THREAD8_EVENT_HANDLE 0x003C1328
#define THREAD8_OBJ 0x003C2678

#elif defined(JPN)

#define FS_OPEN_FILE 0x0022929C
#define GSP_GET_HANDLE 0x0021C960
#define GSP_GET_INTERRUPTRECEIVER 0x001C805C
#define GSP_ENQUEUE_CMD 0x001C7BF4

#define FS_READ_FILE 0x002C40CC
#define GSP_GX_CMD4 0x002E9258
#define GSP_FLUSH_DATA_CACHE 0x002E2818

#define SRV_SESSIONHANDLE 0x00374258
#define SRV_SEMAPHORE 0x00374248

#define THREAD8_EVENT_HANDLE 0x003C12C8
#define THREAD8_OBJ 0x003C2618

#else
#error "Region not supported for this system version range"
#endif
