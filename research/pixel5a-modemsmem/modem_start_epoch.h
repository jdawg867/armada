/* SPDX-License-Identifier: GPL-2.0 */
/*
 * Armada Pixel 5a / SM7250 boot-epoch model, host C11 only.
 * Does not implement an actual remoteproc callback, synchronization,
 * SMEM publication, or modify Linux. Linux 7.2.6 source reference:
 * remoteproc_core.c rproc_add/rproc_trigger_auto_boot/rproc_boot;
 * qcom_q6v5_pas.c qcom_pas_probe/qcom_pas_start.
 */
#ifndef ARMADA_MODEM_START_EPOCH_H
#define ARMADA_MODEM_START_EPOCH_H
#include <errno.h>
#include <stdint.h>
#include <stdbool.h>

enum armada_start_origin {
    ARMADA_START_AUTOMATIC,
    ARMADA_START_EXPLICIT,
    ARMADA_START_RECOVERY
};

struct armada_modem_start_epoch {
    uint64_t epoch;
    uint64_t staged_epoch;
    uint64_t acknowledged_epoch;
    bool staged;
    bool acknowledged;
    bool failed;
};

static inline void armada_start_epoch_init(struct armada_modem_start_epoch *g)
{
    if (!g) return;
    g->epoch = 1;
    g->staged_epoch = 0;
    g->acknowledged_epoch = 0;
    g->staged = false;
    g->acknowledged = false;
    g->failed = false;
}

/* Return a token for a *new* simulated modem generation. */
static inline int armada_start_epoch_restart(struct armada_modem_start_epoch *g,
                                              uint64_t *generation)
{
    if (!g || !generation) return -EINVAL;
    if (g->epoch == UINT64_MAX) return -EOVERFLOW;
    ++g->epoch;
    g->staged_epoch = 0;
    g->acknowledged_epoch = 0;
    g->staged = false;
    g->acknowledged = false;
    g->failed = false;
    *generation = g->epoch;
    return 0;
}

/* Real integration needs a lock and a trusted publication protocol. */
static inline int armada_start_epoch_stage(struct armada_modem_start_epoch *g,
                                           uint64_t generation, int result)
{
    if (!g || generation == 0) return -EINVAL;
    if (generation != g->epoch) return -ESTALE;
    if (g->failed) return -EIO;
    if (result) {
        if (result != -EAGAIN) g->failed = true;
        return result;
    }
    g->staged = true;
    g->staged_epoch = generation;
    g->acknowledged = false;
    g->acknowledged_epoch = 0;
    return 0;
}

static inline int armada_start_epoch_ack(struct armada_modem_start_epoch *g,
                                         uint64_t generation, int result)
{
    if (!g || generation == 0) return -EINVAL;
    if (generation != g->epoch) return -ESTALE;
    if (g->failed) return -EIO;
    if (!g->staged || g->staged_epoch != generation) return -EAGAIN;
    if (result) {
        g->failed = true;
        g->acknowledged = false;
        return result;
    }
    g->acknowledged = true;
    g->acknowledged_epoch = generation;
    return 0;
}

static inline int armada_start_epoch_can_start(const struct armada_modem_start_epoch *g,
                                               enum armada_start_origin origin)
{
    if (!g) return -EINVAL;
    if (origin != ARMADA_START_AUTOMATIC &&
        origin != ARMADA_START_EXPLICIT &&
        origin != ARMADA_START_RECOVERY) return -EINVAL;
    if (g->failed) return -EIO;
    if (!g->staged || !g->acknowledged ||
        g->staged_epoch != g->epoch || g->acknowledged_epoch != g->epoch)
        return -EAGAIN;
    return 0;
}
#endif
