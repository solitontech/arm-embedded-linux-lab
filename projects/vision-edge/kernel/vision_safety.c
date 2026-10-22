// SPDX-License-Identifier: GPL-2.0
/*
 * vision_safety.c — VisionEdge deterministic safety platform driver for BCM2711
 *
 * Binds to the Device Tree node "cortexlab,vision-safety" and provides:
 *   - /dev/vision_safety char device with ioctl + poll interface
 *   - Top-half ISR for sub-10us emergency relay cutoff on GPIO 23 falling edge
 *   - Spinlock-protected state for concurrent ISR + ioctl access
 */
#include <linux/module.h>
#include <linux/platform_device.h>
#include <linux/fs.h>
#include <linux/cdev.h>
#include <linux/io.h>
#include <linux/interrupt.h>
#include <linux/of.h>
#include <linux/uaccess.h>
#include <linux/poll.h>
#include <linux/ktime.h>
#include "include/uapi/vision_safety_uapi.h"

#define DRIVER_NAME "vision_safety"

/* BCM2711 GPIO register offsets (byte offsets from base 0xFE200000) */
#define GPSET0  0x1C   /* Output Set  — write 1 to set pin HIGH   */
#define GPCLR0  0x28   /* Output Clear — write 1 to set pin LOW   */

/* Pin assignments (from Device Tree) */
#define PIN_RELAY   18  /* Interlock relay — active LOW (LOW = energized)  */
#define PIN_SENSOR  23  /* Optical safety sensor — falling edge interrupt  */
#define PIN_STROBE  24  /* Fault strobe LED — active HIGH                  */

/* ─── Device State ─── */

struct vision_safety_dev {
	struct cdev             cdev;
	dev_t                   devt;
	struct class           *cls;
	struct device          *device;
	void __iomem           *base;       /* ioremap'd GPIO register block  */
	int                     irq;
	spinlock_t              lock;
	wait_queue_head_t       wq;
	struct vision_safety_status status;
};

static struct vision_safety_dev *g_vdev;

/* ─── Top-Half ISR (Hard IRQ Context) ───
 *
 * This is the performance-critical path.  When the optical sensor asserts
 * a falling edge on GPIO 23, the GIC-400 routes the interrupt here.
 * We MUST complete the relay cutoff (iowrite32 -> GPSET0 for GPIO 18)
 * in under 10 us.  No sleeping, no allocation, no printk.
 */
static irqreturn_t vision_safety_irq_handler(int irq, void *dev_id)
{
	struct vision_safety_dev *vdev = dev_id;
	unsigned long flags;

	spin_lock_irqsave(&vdev->lock, flags);

	if (vdev->status.armed && !vdev->status.tripped) {
		/* Emergency cutoff: de-energize relay (GPIO 18 HIGH = relay off) */
		iowrite32(1 << PIN_RELAY, vdev->base + GPSET0);
		/* Fault indicator: light strobe (GPIO 24 HIGH) */
		iowrite32(1 << PIN_STROBE, vdev->base + GPSET0);

		vdev->status.tripped = 1;
		vdev->status.trip_count++;
		vdev->status.trip_timestamp_ns = ktime_get_ns();

		wake_up_interruptible(&vdev->wq);
	}

	spin_unlock_irqrestore(&vdev->lock, flags);
	return IRQ_HANDLED;
}

/* ─── File Operations ─── */

static int vision_open(struct inode *inode, struct file *file)
{
	file->private_data = g_vdev;
	return 0;
}

static long vision_ioctl(struct file *file, unsigned int cmd, unsigned long arg)
{
	struct vision_safety_dev *vdev = file->private_data;
	unsigned long flags;

	switch (cmd) {
	case VISION_IOCTL_ARM:
		spin_lock_irqsave(&vdev->lock, flags);
		vdev->status.armed   = 1;
		vdev->status.tripped = 0;
		/* Energize relay (GPIO 18 LOW = active-low relay ON) */
		iowrite32(1 << PIN_RELAY, vdev->base + GPCLR0);
		/* Strobe off */
		iowrite32(1 << PIN_STROBE, vdev->base + GPCLR0);
		spin_unlock_irqrestore(&vdev->lock, flags);
		break;

	case VISION_IOCTL_DISARM:
		spin_lock_irqsave(&vdev->lock, flags);
		vdev->status.armed   = 0;
		vdev->status.tripped = 0;
		/* De-energize relay (GPIO 18 HIGH = relay off) */
		iowrite32(1 << PIN_RELAY, vdev->base + GPSET0);
		/* Strobe off */
		iowrite32(1 << PIN_STROBE, vdev->base + GPCLR0);
		spin_unlock_irqrestore(&vdev->lock, flags);
		break;

	case VISION_IOCTL_TRIP:
		spin_lock_irqsave(&vdev->lock, flags);
		if (vdev->status.armed && !vdev->status.tripped) {
			/* Software-initiated trip — same cutoff as ISR */
			iowrite32(1 << PIN_RELAY, vdev->base + GPSET0);
			iowrite32(1 << PIN_STROBE, vdev->base + GPSET0);
			vdev->status.tripped = 1;
			vdev->status.trip_count++;
			vdev->status.trip_timestamp_ns = ktime_get_ns();
		}
		spin_unlock_irqrestore(&vdev->lock, flags);
		wake_up_interruptible(&vdev->wq);
		break;

	case VISION_IOCTL_STATUS:
		if (copy_to_user((void __user *)arg, &vdev->status,
				 sizeof(vdev->status)))
			return -EFAULT;
		break;

	default:
		return -ENOTTY;
	}

	return 0;
}

static __poll_t vision_poll(struct file *file, struct poll_table_struct *wait)
{
	struct vision_safety_dev *vdev = file->private_data;
	__poll_t mask = 0;

	poll_wait(file, &vdev->wq, wait);

	if (vdev->status.tripped)
		mask |= EPOLLIN | EPOLLPRI;

	return mask;
}

static const struct file_operations vision_fops = {
	.owner          = THIS_MODULE,
	.open           = vision_open,
	.unlocked_ioctl = vision_ioctl,
	.poll           = vision_poll,
};

/* ─── Platform Driver Probe / Remove ─── */

static int vision_probe(struct platform_device *pdev)
{
	struct resource *res;
	int ret;

	g_vdev = devm_kzalloc(&pdev->dev, sizeof(*g_vdev), GFP_KERNEL);
	if (!g_vdev)
		return -ENOMEM;

	spin_lock_init(&g_vdev->lock);
	init_waitqueue_head(&g_vdev->wq);

	/* Map the GPIO register block (0xFE200000, 4 KiB) */
	res = platform_get_resource(pdev, IORESOURCE_MEM, 0);
	g_vdev->base = devm_ioremap_resource(&pdev->dev, res);
	if (IS_ERR(g_vdev->base))
		return PTR_ERR(g_vdev->base);

	/* Register falling-edge IRQ on GPIO 23 */
	g_vdev->irq = platform_get_irq(pdev, 0);
	if (g_vdev->irq > 0) {
		ret = devm_request_irq(&pdev->dev, g_vdev->irq,
				       vision_safety_irq_handler,
				       IRQF_TRIGGER_FALLING, DRIVER_NAME, g_vdev);
		if (ret)
			dev_warn(&pdev->dev, "IRQ %d registration failed: %d\n",
				 g_vdev->irq, ret);
	}

	/* Create /dev/vision_safety char device */
	alloc_chrdev_region(&g_vdev->devt, 0, 1, DRIVER_NAME);
	cdev_init(&g_vdev->cdev, &vision_fops);
	cdev_add(&g_vdev->cdev, g_vdev->devt, 1);

	g_vdev->cls    = class_create(DRIVER_NAME);
	g_vdev->device = device_create(g_vdev->cls, NULL, g_vdev->devt,
				       NULL, DRIVER_NAME);

	platform_set_drvdata(pdev, g_vdev);
	dev_info(&pdev->dev,
		 "vision_safety: platform driver bound (IRQ %d)\n", g_vdev->irq);

	return 0;
}

static void vision_remove(struct platform_device *pdev)
{
	struct vision_safety_dev *vdev = platform_get_drvdata(pdev);

	device_destroy(vdev->cls, vdev->devt);
	class_destroy(vdev->cls);
	cdev_del(&vdev->cdev);
	unregister_chrdev_region(vdev->devt, 1);

	dev_info(&pdev->dev, "vision_safety: removed\n");
}

/* ─── Device Tree Match Table ─── */

static const struct of_device_id vision_of_match[] = {
	{ .compatible = "cortexlab,vision-safety" },
	{ /* sentinel */ }
};
MODULE_DEVICE_TABLE(of, vision_of_match);

static struct platform_driver vision_driver = {
	.probe  = vision_probe,
	.remove = vision_remove,
	.driver = {
		.name           = DRIVER_NAME,
		.of_match_table = vision_of_match,
	},
};
module_platform_driver(vision_driver);

MODULE_LICENSE("GPL");
MODULE_AUTHOR("ARM Embedded Linux Lab");
MODULE_DESCRIPTION("VisionEdge deterministic safety platform driver for BCM2711");
