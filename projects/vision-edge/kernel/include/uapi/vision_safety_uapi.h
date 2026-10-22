/* kernel/include/uapi/vision_safety_uapi.h
 *
 * Shared UAPI header — used by both the kernel module and userspace DriverClient.
 * Defines ioctl command numbers and the status struct that crosses the
 * kernel-user boundary via copy_to_user().
 */
#ifndef _UAPI_VISION_SAFETY_H
#define _UAPI_VISION_SAFETY_H

#ifdef __KERNEL__
#include <linux/ioctl.h>
#include <linux/types.h>
#else
#include <sys/ioctl.h>
#include <stdint.h>
typedef uint32_t __u32;
typedef uint64_t __u64;
#endif

#define VISION_SAFETY_MAGIC 'V'

struct vision_safety_status {
    __u32 armed;             /* 1 = system armed, relay energized       */
    __u32 tripped;           /* 1 = safety breach detected              */
    __u64 trip_timestamp_ns; /* ktime_get_ns() at moment of trip        */
    __u32 trip_count;        /* cumulative trip counter (since insmod)   */
};

#define VISION_IOCTL_ARM    _IO(VISION_SAFETY_MAGIC,  0x01) /* Arm: energize relay          */
#define VISION_IOCTL_DISARM _IO(VISION_SAFETY_MAGIC,  0x02) /* Disarm: de-energize relay    */
#define VISION_IOCTL_TRIP   _IO(VISION_SAFETY_MAGIC,  0x03) /* Software trip: emergency cut */
#define VISION_IOCTL_STATUS _IOR(VISION_SAFETY_MAGIC, 0x04, struct vision_safety_status)

#endif /* _UAPI_VISION_SAFETY_H */
