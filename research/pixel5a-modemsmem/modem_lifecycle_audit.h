/* SPDX-License-Identifier: GPL-2.0 */
/*
 * Host-only lifecycle extension for the Step 782 simulated start epoch.
 * NOT synchronized with Linux rproc locks, not a remoteproc callback.
 * Event handlers invalidate simulated readiness. State MUST NOT be treated
 * as authority for real Qualcomm MPSS boot or recovery.
 */
#ifndef ARMADA_MODEM_LIFECYCLE_AUDIT_H
#define ARMADA_MODEM_LIFECYCLE_AUDIT_H

#include "modem_start_epoch.h"

struct armada_modem_lifecycle_audit {
    struct armada_modem_start_epoch gate;
    bool deleting;
    bool crashed;
};

static inline void armada_lifecycle_init(struct armada_modem_lifecycle_audit *ctx)
{
    if (!ctx) return;
    armada_start_epoch_init(&ctx->gate);
    ctx->deleting = false;
    ctx->crashed = false;
}

/* Simulated crash revokes readiness in a new generation. */
static inline int armada_lifecycle_crash(struct armada_modem_lifecycle_audit *ctx,
                                         uint64_t *new_generation)
{
    if (!ctx || !new_generation) return -EINVAL;
    if (ctx->deleting) return -ENODEV;
    if (ctx->crashed) return -EALREADY;
    /* On overflow, do not publish a new state and do not falsely authorize. */
    if (ctx->gate.epoch == UINT64_MAX) return -EOVERFLOW;
    ctx->crashed = true;
    return armada_start_epoch_restart(&ctx->gate, new_generation);
}

/* Simulated removal remains terminal until a fresh init of a NEW object. */
static inline int armada_lifecycle_remove(struct armada_modem_lifecycle_audit *ctx)
{
    if (!ctx) return -EINVAL;
    ctx->deleting = true;
    ctx->crashed = false;
    ctx->gate.staged = false;
    ctx->gate.acknowledged = false;
    ctx->gate.staged_epoch = 0;
    ctx->gate.acknowledged_epoch = 0;
    ctx->gate.failed = true;
    return 0;
}

/* These are simulations: no real recovery, firmware or SMEM occurs here. */
static inline int armada_lifecycle_ack(struct armada_modem_lifecycle_audit *ctx,
                                       uint64_t generation, int result)
{
    if (!ctx) return -EINVAL;
    if (ctx->deleting) return -ENODEV;
    return armada_start_epoch_ack(&ctx->gate, generation, result);
}
static inline int armada_lifecycle_stage(struct armada_modem_lifecycle_audit *ctx,
                                         uint64_t generation, int result)
{
    if (!ctx) return -EINVAL;
    if (ctx->deleting) return -ENODEV;
    return armada_start_epoch_stage(&ctx->gate, generation, result);
}
static inline int armada_lifecycle_start(const struct armada_modem_lifecycle_audit *ctx,
                                         enum armada_start_origin origin)
{
    if (!ctx) return -EINVAL;
    if (ctx->deleting) return -ENODEV;
    return armada_start_epoch_can_start(&ctx->gate, origin);
}
static inline int armada_lifecycle_resume_from_crash(struct armada_modem_lifecycle_audit *ctx)
{
    if (!ctx) return -EINVAL;
    if (ctx->deleting) return -ENODEV;
    if (!ctx->crashed) return -EINVAL;
    if (armada_start_epoch_can_start(&ctx->gate, ARMADA_START_RECOVERY))
        return -EAGAIN;
    ctx->crashed = false;
    return 0;
}
#endif
