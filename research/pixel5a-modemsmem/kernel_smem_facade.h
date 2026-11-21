/* SPDX-License-Identifier: GPL-2.0 */
/*
 * Experimental Linux-facing error translation only.
 * NOT connected to any Kconfig, driver, DT node, modem, or publication path.
 * Test with a deliberately minimal mocked Linux include tree. Kernel
 * compilation and actual Linux error-pointer semantics still require review.
 */
#ifndef ARMADA_MODEMSMEM_KERNEL_SMEM_FACADE_H
#define ARMADA_MODEMSMEM_KERNEL_SMEM_FACADE_H

#include <linux/err.h>
#include <linux/errno.h>
#include <linux/types.h>
#include <linux/soc/qcom/smem.h>

/* Never dereference a kernel ERR_PTR; preserve the original negative errno. */
static inline int armada_modemsmem_kernel_get(unsigned item,
                                              const void **out,
                                              size_t *out_size)
{
    void *p;
    size_t count = 0;

    if (!out || !out_size)
        return -EINVAL;
    p = qcom_smem_get(QCOM_SMEM_HOST_ANY, item, &count);
    if (IS_ERR(p))
        return PTR_ERR(p);
    if (!p)
        return -ENODATA;
    *out = p;
    *out_size = count;
    return 0;
}

/* Allocating is a separate operation with integer errno return semantics. */
static inline int armada_modemsmem_kernel_alloc(unsigned item, size_t size)
{
    return qcom_smem_alloc(QCOM_SMEM_HOST_ANY, item, size);
}
#endif
