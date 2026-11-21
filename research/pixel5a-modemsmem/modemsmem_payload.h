/* SPDX-License-Identifier: GPL-2.0 */
/*
 * Armada research-only Pixel modemsmem payload format and builder.
 * Not wired to Linux Kconfig, DT, remoteproc, or real SMEM writes.
 * Source layout: LineageOS redbull modemsmem.h blob
 * a6b9d991fe7c023f44c21cc5c597746414c532a2.
 */
#ifndef ARMADA_PIXEL5A_MODEMSMEM_PAYLOAD_H
#define ARMADA_PIXEL5A_MODEMSMEM_PAYLOAD_H

#include <stdint.h>
#include <stddef.h>
#include <string.h>
#include <errno.h>

#define ARMADA_MODEMSMEM_ITEM 134U
#define ARMADA_MODEMSMEM_VERSION 0U
#define ARMADA_MODEMSMEM_FTM_MAGIC UINT32_C(0x6846544d)
#define ARMADA_MODEMSMEM_DSDS_MAGIC UINT32_C(0x44534453)

/* Order and size intentionally match the 16-u32 downstream vendor ABI. */
struct armada_modemsmem_payload {
    uint32_t version;
    uint32_t reserved_1;
    uint32_t major_id;
    uint32_t minor_id;
    uint32_t subtype;
    uint32_t platform;
    uint32_t reserved_2;
    uint32_t ftm_magic;
    uint32_t efs_magic;
    uint32_t modem_flag;
    uint32_t dsds_magic;
    uint32_t reserved_3[5];
};

struct armada_modemsmem_inputs {
    uint32_t platform_version;
    uint32_t platform_type;
    uint32_t platform_subtype;
    uint32_t modem_flag;
    /* Factory and DSDS are explicit inputs; never auto-enable them. */
    int factory_mode;
    int dsds_mode;
};

_Static_assert(sizeof(struct armada_modemsmem_payload) == 64,
               "downstream SMEM vendor item must be 64 bytes");
_Static_assert(offsetof(struct armada_modemsmem_payload, modem_flag) == 36,
               "modem flag offset must match downstream");
_Static_assert(offsetof(struct armada_modemsmem_payload, dsds_magic) == 40,
               "DSDS offset must match downstream");

/*
 * Builds an in-memory payload; no SMEM allocation or publication occurs.
 * Preserves the downstream driver's 8-bit major/minor extraction.
 * All other words are explicitly zeroed before assignment.
 */
static inline int armada_modemsmem_build(
    struct armada_modemsmem_payload *out,
    const struct armada_modemsmem_inputs *in)
{
    if (!out || !in)
        return -EINVAL;

    memset(out, 0, sizeof(*out));
    out->version = ARMADA_MODEMSMEM_VERSION;
    out->major_id = (in->platform_version >> 16) & UINT32_C(0xff);
    out->minor_id = in->platform_version & UINT32_C(0xff);
    out->platform = in->platform_type;
    out->subtype = in->platform_subtype;
    out->modem_flag = in->modem_flag;
    if (in->factory_mode)
        out->ftm_magic = ARMADA_MODEMSMEM_FTM_MAGIC;
    if (in->dsds_mode)
        out->dsds_magic = ARMADA_MODEMSMEM_DSDS_MAGIC;
    return 0;
}

#endif
