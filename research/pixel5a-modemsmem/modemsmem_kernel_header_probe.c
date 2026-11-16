// SPDX-License-Identifier: GPL-2.0
/*
 * Compile-only header/API probe for exact Linux 7.2.6.
 * Intentionally no module_init, platform_driver registration,
 * device-tree match, SMEM write, firmware request or remoteproc operation.
 *
 * The external Kbuild target may produce an object/module artifact in CI;
 * the CI never uploads, installs, signs or runs such an artifact.
 */
#include <linux/build_bug.h>
#include <linux/err.h>
#include <linux/errno.h>
#include <linux/module.h>
#include <linux/stddef.h>
#include <linux/soc/qcom/socinfo.h>
#include <linux/soc/qcom/smem.h>
#include "kernel_smem_facade.h"

static_assert(SMEM_HW_SW_BUILD_ID == 137);
static_assert(offsetof(struct socinfo, fmt) == 0);
static_assert(offsetof(struct socinfo, hw_plat) == 52);
static_assert(offsetof(struct socinfo, plat_ver) == 56);
static_assert(offsetof(struct socinfo, hw_plat_subtype) == 64);
static_assert(sizeof(struct socinfo) >= 68);

/*
 * Force compile-time signature checking against real kernel declarations.
 * No function is called at runtime. The function itself is not registered.
 */
static int __maybe_unused armada_modemsmem_kernel_api_probe(void)
{
    const void *ptr = NULL;
    size_t length = 0;
    int ret;

    ret = armada_modemsmem_kernel_get(SMEM_HW_SW_BUILD_ID, &ptr, &length);
    if (ret)
        return ret;
    if (length < 68)
        return -EMSGSIZE;

    return armada_modemsmem_kernel_alloc(134, 64);
}

MODULE_LICENSE("GPL");
MODULE_DESCRIPTION("Armada Pixel 5a compile-only SMEM header probe (not deployed)");
