/* SPDX-License-Identifier: GPL-2.0 */
/*
 * Armada / Pixel 5a modem start *simulation* only.
 * No real remoteproc, Kconfig, DT, SMEM write or firmware integration.
 *
 * A success acknowledgement from the caller only changes this test model.
 * The kernel's actual qcom_q6v5_pas start path does NOT consult this gate.
 */
#ifndef ARMADA_MODEM_BOOT_GATE_H
#define ARMADA_MODEM_BOOT_GATE_H

#include <errno.h>

enum armada_modem_boot_phase {
    ARMADA_MODEM_WAIT_SMEM,
    ARMADA_MODEM_STAGED,
    ARMADA_MODEM_READY_SIMULATED,
    ARMADA_MODEM_FAILED
};

struct armada_modem_boot_gate {
    enum armada_modem_boot_phase phase;
    int last_error;
};

static inline void armada_modem_boot_gate_reset(struct armada_modem_boot_gate *gate)
{
    if (!gate)
        return;
    gate->phase = ARMADA_MODEM_WAIT_SMEM;
    gate->last_error = 0;
}

/*
 * Stage result is returned by the source-only Socinfo + SMEM staging test.
 * -EAGAIN is the host stand-in for Linux -EPROBE_DEFER.
 * All other errors block progress until an explicit reset.
 */
static inline int armada_modem_boot_gate_stage(
    struct armada_modem_boot_gate *gate, int result)
{
    if (!gate)
        return -EINVAL;
    if (gate->phase != ARMADA_MODEM_WAIT_SMEM)
        return -EBUSY;
    if (result == 0) {
        gate->phase = ARMADA_MODEM_STAGED;
        gate->last_error = 0;
        return 0;
    }
    gate->last_error = result;
    if (result != -EAGAIN)
        gate->phase = ARMADA_MODEM_FAILED;
    return result;
}

/*
 * This models an external acknowledgement ONLY. We intentionally provide
 * no SMEM publication function and do not claim such an ack exists in Linux.
 */
static inline int armada_modem_boot_gate_ack_publication(
    struct armada_modem_boot_gate *gate, int result)
{
    if (!gate)
        return -EINVAL;
    if (gate->phase != ARMADA_MODEM_STAGED)
        return -EAGAIN;
    if (result == 0) {
        gate->phase = ARMADA_MODEM_READY_SIMULATED;
        gate->last_error = 0;
        return 0;
    }
    gate->phase = ARMADA_MODEM_FAILED;
    gate->last_error = result;
    return result;
}

/* A simulated request only: no code here can start a remote processor. */
static inline int armada_modem_boot_gate_request_start(
    const struct armada_modem_boot_gate *gate)
{
    if (!gate)
        return -EINVAL;
    if (gate->phase == ARMADA_MODEM_READY_SIMULATED)
        return 0;
    if (gate->phase == ARMADA_MODEM_FAILED)
        return gate->last_error ? gate->last_error : -EIO;
    return -EAGAIN;
}

#endif
