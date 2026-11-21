/* SPDX-License-Identifier: GPL-2.0 */
/*
 * Pixel 5a source-only ARM64 Linux 7.2.6 SMEM preflight.
 * This helper is not registered, called by an active driver or linked into
 * a phone kernel. No SMEM writes, allocations or modem start are performed.
 *
 * Reads SOCINFO item 137 and *requires an already existing* vendor item 134.
 * Requiring 134 is a deliberate fail-closed ownership policy, not a claim
 * that item 134 is allocated before the real Pixel 5a modem starts.
 */
#ifndef ARMADA_PIXEL5A_KERNEL_READONLY_PREFLIGHT_H
#define ARMADA_PIXEL5A_KERNEL_READONLY_PREFLIGHT_H

#include <linux/build_bug.h>
#include <linux/errno.h>
#include <linux/string.h>
#include <linux/types.h>
#include <linux/unaligned.h>
#include <linux/soc/qcom/socinfo.h>
#include "kernel_smem_facade.h"

#define ARMADA_VENDOR_SMEM_ITEM 134U
#define ARMADA_VENDOR_SMEM_LENGTH 64U
#define ARMADA_SOCINFO_PREFIX_LENGTH 68U

/*
 * Host-endian *candidate*, never a published wire payload. The field-to-wire
 * conversion, ownership, locking and publication are explicitly NOT designed.
 */
struct armada_pixel5a_candidate {
    u32 major_id;
    u32 minor_id;
    u32 platform;
    u32 subtype;
};

static inline int armada_pixel5a_readonly_preflight(
    struct armada_pixel5a_candidate *result)
{
    const void *soc_ptr = NULL, *vendor_ptr = NULL;
    u8 prefix[ARMADA_SOCINFO_PREFIX_LENGTH];
    struct armada_pixel5a_candidate candidate;
    size_t soc_size = 0, vendor_size = 0;
    u32 fmt, version;
    int ret;

    if (!result)
        return -EINVAL;

    ret = armada_modemsmem_kernel_get(SMEM_HW_SW_BUILD_ID,
                                      &soc_ptr, &soc_size);
    if (ret)
        return ret;
    if (soc_size < sizeof(prefix))
        return -EMSGSIZE;

    /*
     * The temporary copy avoids parsing via unaligned typed dereferences.
     * It does not establish concurrent SMEM writer / teardown guarantees.
     */
    memcpy(prefix, soc_ptr, sizeof(prefix));
    fmt = get_unaligned_le32(prefix);
    if ((fmt >> 16) != 0 || (fmt & 0xffffU) < 6 ||
        (fmt & 0xffffU) > 23)
        return -EOPNOTSUPP;

    version = get_unaligned_le32(prefix + 56);
    candidate.major_id = (version >> 16) & 0xffU;
    candidate.minor_id = version & 0xffU;
    candidate.platform = get_unaligned_le32(prefix + 52);
    candidate.subtype = get_unaligned_le32(prefix + 64);

    /* Existing data is not ours to initialize, overwrite or free. */
    ret = armada_modemsmem_kernel_get(ARMADA_VENDOR_SMEM_ITEM,
                                      &vendor_ptr, &vendor_size);
    if (ret)
        return ret;
    if (vendor_size != ARMADA_VENDOR_SMEM_LENGTH)
        return -EMSGSIZE;

    *result = candidate;
    return 0;
}
#endif
