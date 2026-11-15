/* SPDX-License-Identifier: GPL-2.0 */
/*
 * Source-only ARMADA SM7250 Socinfo -> modemsmem staging adapter.
 * Host-buildable C11 reference; NOT a Linux kernel module or runtime driver.
 * Source contracts: Linux 7.2.6 smem.h/socinfo.h at 500df175a7f9e6bc.
 */
#ifndef ARMADA_PIXEL5A_MODEMSMEM_ADAPTER_H
#define ARMADA_PIXEL5A_MODEMSMEM_ADAPTER_H

#include "modemsmem_payload.h"

/* From the pinned include/linux/soc/qcom/socinfo.h. */
#define ARMADA_SOCINFO_ITEM 137U
#define ARMADA_SOCINFO_MIN_FORMAT ((uint32_t)6)
#define ARMADA_SOCINFO_MAX_REVIEWED_FORMAT ((uint32_t)23)
#define ARMADA_SMEM_HOST_ANY ((unsigned)-1)

/*
 * The pinned struct socinfo layout, encoded as little-endian bytes:
 * fmt [0:4], id [4:8], ver [8:12], build_id [12:44],
 * raw_id [44:48], raw_ver [48:52], hw_plat [52:56],
 * plat_ver [56:60], accessory_chip [60:64],
 * hw_plat_subtype [64:68].
 * Format must indicate version >= 6 before accessing subtype.
 */
#define ARMADA_SOCINFO_REQUIRED_SIZE 68U

struct armada_modemsmem_ops {
    /*
     * A *host-only* error-normalized adapter signature. A kernel wrapper
     * would convert IS_ERR/PTR_ERR from qcom_smem_get() into int and avoid
     * dereferencing invalid pointers. No such wrapper is implemented here.
     */
    int (*read_item)(void *context, unsigned host, unsigned item,
                     const unsigned char **data, size_t *length);
    int (*alloc_item)(void *context, unsigned host, unsigned item, size_t length);
    int (*inspect_item)(void *context, unsigned host, unsigned item,
                        const void **data, size_t *length);
    void *context;
};

/* Decode a bounded, reviewed version of the mainline SoCinfo wire format. */
static inline uint32_t armada_read_le32(const unsigned char *p)
{
    return ((uint32_t)p[0]) | ((uint32_t)p[1] << 8) |
           ((uint32_t)p[2] << 16) | ((uint32_t)p[3] << 24);
}

static inline int armada_modemsmem_socinfo_inputs(
    const unsigned char *bytes, size_t length,
    struct armada_modemsmem_inputs *out)
{
    uint32_t fmt;
    if (!bytes || !out)
        return -EINVAL;
    if (length < 4)
        return -EMSGSIZE;
    fmt = armada_read_le32(bytes);
    /* Only format 0.6..0.23 has been reviewed for these field offsets. */
    if ((fmt >> 16) != 0 || (fmt & 0xffff) < ARMADA_SOCINFO_MIN_FORMAT ||
        (fmt & 0xffff) > ARMADA_SOCINFO_MAX_REVIEWED_FORMAT)
        return -EOPNOTSUPP;
    if (length < ARMADA_SOCINFO_REQUIRED_SIZE)
        return -EMSGSIZE;
    /* Do not modify caller output on failure. */
    {
        struct armada_modemsmem_inputs temp = {0};
        temp.platform_version = armada_read_le32(bytes + 56);
        temp.platform_type = armada_read_le32(bytes + 52);
        temp.platform_subtype = armada_read_le32(bytes + 64);
        *out = temp; /* modem_flag, factory, DSDS default to off. */
    }
    return 0;
}

/*
 * Prepare a candidate payload without publishing to SMEM.
 * Validates existing vendor item 134 allocation/size, including -EEXIST.
 * No writes to item 134 or modem, no ownership/lifetime guarantee.
 */
static inline int armada_modemsmem_stage(
    const struct armada_modemsmem_ops *ops,
    struct armada_modemsmem_payload *output)
{
    struct armada_modemsmem_inputs inputs;
    struct armada_modemsmem_payload staged;
    const unsigned char *soc = NULL;
    const void *vendor = NULL;
    size_t soc_len = 0, vendor_len = 0;
    int ret;

    if (!ops || !output || !ops->read_item ||
        !ops->alloc_item || !ops->inspect_item)
        return -EINVAL;
    ret = ops->read_item(ops->context, ARMADA_SMEM_HOST_ANY,
                         ARMADA_SOCINFO_ITEM, &soc, &soc_len);
    if (ret)
        return ret;
    ret = armada_modemsmem_socinfo_inputs(soc, soc_len, &inputs);
    if (ret)
        return ret;
    ret = armada_modemsmem_build(&staged, &inputs);
    if (ret)
        return ret;
    ret = ops->alloc_item(ops->context, ARMADA_SMEM_HOST_ANY,
                          ARMADA_MODEMSMEM_ITEM, sizeof(staged));
    if (ret && ret != -EEXIST)
        return ret;
    ret = ops->inspect_item(ops->context, ARMADA_SMEM_HOST_ANY,
                            ARMADA_MODEMSMEM_ITEM, &vendor, &vendor_len);
    if (ret)
        return ret;
    if (!vendor || vendor_len != sizeof(staged))
        return -EMSGSIZE;
    *output = staged;
    return 0;
}
#endif
