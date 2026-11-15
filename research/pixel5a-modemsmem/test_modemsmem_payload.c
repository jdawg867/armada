/* SPDX-License-Identifier: GPL-2.0 */
/* Host-executed tests for the source-only vendor ABI payload builder. */
#include <assert.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include "modemsmem_payload.h"

static void basic_layout(void)
{
    assert(ARMADA_MODEMSMEM_ITEM == 134U);
    assert(sizeof(struct armada_modemsmem_payload) == 64);
    assert(offsetof(struct armada_modemsmem_payload, major_id) == 8);
    assert(offsetof(struct armada_modemsmem_payload, minor_id) == 12);
    assert(offsetof(struct armada_modemsmem_payload, subtype) == 16);
    assert(offsetof(struct armada_modemsmem_payload, platform) == 20);
    assert(offsetof(struct armada_modemsmem_payload, ftm_magic) == 28);
    assert(offsetof(struct armada_modemsmem_payload, modem_flag) == 36);
    assert(offsetof(struct armada_modemsmem_payload, dsds_magic) == 40);
    puts("PASS 64-byte vendor SMEM item and field offsets");
}

static void normal_mode(void)
{
    struct armada_modemsmem_inputs in = {
        .platform_version = UINT32_C(0xabcd1234),
        .platform_type = 42,
        .platform_subtype = 7,
        .modem_flag = UINT32_C(0x12345678)
    };
    struct armada_modemsmem_payload out;
    memset(&out, 0xff, sizeof(out));
    assert(armada_modemsmem_build(&out, &in) == 0);
    assert(out.version == 0 && out.major_id == 0xcd && out.minor_id == 0x34);
    assert(out.platform == 42 && out.subtype == 7);
    assert(out.modem_flag == UINT32_C(0x12345678));
    assert(out.ftm_magic == 0 && out.dsds_magic == 0 && out.efs_magic == 0);
    assert(out.reserved_1 == 0 && out.reserved_2 == 0);
    for (size_t i = 0; i < 5; i++)
        assert(out.reserved_3[i] == 0);
    puts("PASS explicit normal mode preserves downstream 8-bit version semantics");
}

static void opt_in_factory_dsds(void)
{
    struct armada_modemsmem_inputs in = {
        .platform_version = UINT32_C(0x00010002),
        .factory_mode = 1,
        .dsds_mode = 1,
    };
    struct armada_modemsmem_payload out;
    assert(armada_modemsmem_build(&out, &in) == 0);
    assert(out.ftm_magic == ARMADA_MODEMSMEM_FTM_MAGIC);
    assert(out.dsds_magic == ARMADA_MODEMSMEM_DSDS_MAGIC);
    assert(out.efs_magic == 0);
    puts("PASS factory and DSDS require explicit opt-in");
}

static void replay_clears_old_flags(void)
{
    struct armada_modemsmem_inputs in = {
        .factory_mode = 1,
        .dsds_mode = 1
    };
    struct armada_modemsmem_payload out;
    assert(armada_modemsmem_build(&out, &in) == 0);
    in.factory_mode = 0;
    in.dsds_mode = 0;
    assert(armada_modemsmem_build(&out, &in) == 0);
    assert(out.ftm_magic == 0 && out.dsds_magic == 0);
    puts("PASS repeated build zeroes stale flags");
}

static void null_rejected(void)
{
    struct armada_modemsmem_inputs in = {0};
    struct armada_modemsmem_payload out;
    assert(armada_modemsmem_build(NULL, &in) == -EINVAL);
    assert(armada_modemsmem_build(&out, NULL) == -EINVAL);
    puts("PASS null input and output rejected");
}

int main(void)
{
    basic_layout();
    normal_mode();
    opt_in_factory_dsds();
    replay_clears_old_flags();
    null_rejected();
    return 0;
}
