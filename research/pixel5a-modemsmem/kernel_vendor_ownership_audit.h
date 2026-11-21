/* SPDX-License-Identifier: GPL-2.0 */
/*
 * Source-only modemsmem ownership preflight for pinned Linux 7.2.6.
 * Classifies *observed* item 134, NOT its owner. Never creates, writes,
 * frees, zeroes, registers or publishes an SMEM item.
 *
 * A successful lookup is NOT proof of permission to mutate memory.
 */
#ifndef ARMADA_PIXEL5A_VENDOR_ITEM_OWNERSHIP_AUDIT_H
#define ARMADA_PIXEL5A_VENDOR_ITEM_OWNERSHIP_AUDIT_H

#include <linux/errno.h>
#include <linux/types.h>
#include "kernel_smem_facade.h"

#define ARMADA_VENDOR_AUDIT_ITEM 134U
#define ARMADA_VENDOR_AUDIT_SIZE 64U

enum armada_vendor_item_observation {
    ARMADA_VENDOR_NOT_CHECKED,
    ARMADA_VENDOR_PRESENT_UNOWNED,
    ARMADA_VENDOR_ABSENT_UNOWNED,
    ARMADA_VENDOR_UNAVAILABLE,
    ARMADA_VENDOR_INVALID_SIZE,
    ARMADA_VENDOR_OTHER_ERROR,
};

struct armada_vendor_item_audit {
    enum armada_vendor_item_observation observation;
    int lookup_errno;
    size_t observed_size;
};

/*
 * Return 0 for a successful audit, including an ABSENT observation.
 * Missing vendor data is NOT a readiness success. The caller must inspect
 * observation and never infer allocation or ownership authorization.
 *
 * -EPROBE_DEFER is preserved as a negative return for actual probe use.
 * -ENXIO and -ENOENT reflect absent item under reviewed Linux 7.2.6 paths.
 */
static inline int armada_vendor_item_inspect(struct armada_vendor_item_audit *out)
{
    struct armada_vendor_item_audit record = {
        .observation = ARMADA_VENDOR_NOT_CHECKED,
    };
    const void *ptr = NULL;
    size_t length = 0;
    int ret;

    if (!out)
        return -EINVAL;

    ret = armada_modemsmem_kernel_get(ARMADA_VENDOR_AUDIT_ITEM, &ptr, &length);
    if (ret == -EPROBE_DEFER) {
        record.observation = ARMADA_VENDOR_UNAVAILABLE;
        record.lookup_errno = ret;
        *out = record;
        return ret;
    }
    if (ret == -ENXIO || ret == -ENOENT) {
        record.observation = ARMADA_VENDOR_ABSENT_UNOWNED;
        record.lookup_errno = ret;
        *out = record;
        return 0;
    }
    if (ret) {
        record.observation = ARMADA_VENDOR_OTHER_ERROR;
        record.lookup_errno = ret;
        *out = record;
        return ret;
    }
    record.observed_size = length;
    if (length != ARMADA_VENDOR_AUDIT_SIZE) {
        record.observation = ARMADA_VENDOR_INVALID_SIZE;
        *out = record;
        return -EMSGSIZE;
    }
    record.observation = ARMADA_VENDOR_PRESENT_UNOWNED;
    *out = record;
    return 0;
}
#endif
