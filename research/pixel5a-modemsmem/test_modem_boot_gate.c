/* SPDX-License-Identifier: GPL-2.0 */
#include <assert.h>
#include <errno.h>
#include <stdio.h>
#include "modem_boot_gate.h"

static void initial_start_denied(void)
{
    struct armada_modem_boot_gate gate;
    armada_modem_boot_gate_reset(&gate);
    assert(armada_modem_boot_gate_request_start(&gate) == -EAGAIN);
    puts("PASS uninitialized stage denies simulated start");
}
static void deferred_still_denied(void)
{
    struct armada_modem_boot_gate gate;
    armada_modem_boot_gate_reset(&gate);
    assert(armada_modem_boot_gate_stage(&gate, -EAGAIN) == -EAGAIN);
    assert(gate.phase == ARMADA_MODEM_WAIT_SMEM);
    assert(armada_modem_boot_gate_request_start(&gate) == -EAGAIN);
    puts("PASS deferred SMEM cannot allow simulated start");
}
static void retry_after_defer(void)
{
    struct armada_modem_boot_gate gate;
    armada_modem_boot_gate_reset(&gate);
    assert(armada_modem_boot_gate_stage(&gate, -EAGAIN) == -EAGAIN);
    assert(armada_modem_boot_gate_stage(&gate, 0) == 0);
    assert(gate.phase == ARMADA_MODEM_STAGED);
    assert(armada_modem_boot_gate_request_start(&gate) == -EAGAIN);
    puts("PASS staged data alone cannot allow simulated start");
}
static void acknowledgement_requires_stage(void)
{
    struct armada_modem_boot_gate gate;
    armada_modem_boot_gate_reset(&gate);
    assert(armada_modem_boot_gate_ack_publication(&gate, 0) == -EAGAIN);
    assert(armada_modem_boot_gate_request_start(&gate) == -EAGAIN);
    puts("PASS publication acknowledgement cannot skip staging");
}
static void explicit_ack_allows_simulation(void)
{
    struct armada_modem_boot_gate gate;
    armada_modem_boot_gate_reset(&gate);
    assert(armada_modem_boot_gate_stage(&gate, 0) == 0);
    assert(armada_modem_boot_gate_ack_publication(&gate, 0) == 0);
    assert(gate.phase == ARMADA_MODEM_READY_SIMULATED);
    assert(armada_modem_boot_gate_request_start(&gate) == 0);
    puts("PASS simulated ready only after successful stage and mock acknowledgement");
}
static void permanent_stage_failure(void)
{
    struct armada_modem_boot_gate gate;
    armada_modem_boot_gate_reset(&gate);
    assert(armada_modem_boot_gate_stage(&gate, -EIO) == -EIO);
    assert(gate.phase == ARMADA_MODEM_FAILED);
    assert(armada_modem_boot_gate_stage(&gate, 0) == -EBUSY);
    assert(armada_modem_boot_gate_request_start(&gate) == -EIO);
    puts("PASS stage error blocks simulated start and unsafe retry");
}
static void failed_publish(void)
{
    struct armada_modem_boot_gate gate;
    armada_modem_boot_gate_reset(&gate);
    assert(armada_modem_boot_gate_stage(&gate, 0) == 0);
    assert(armada_modem_boot_gate_ack_publication(&gate, -EIO) == -EIO);
    assert(armada_modem_boot_gate_request_start(&gate) == -EIO);
    assert(armada_modem_boot_gate_ack_publication(&gate, 0) == -EAGAIN);
    puts("PASS failed mock publication denies start");
}
static void reset_revokes_readiness(void)
{
    struct armada_modem_boot_gate gate;
    armada_modem_boot_gate_reset(&gate);
    assert(armada_modem_boot_gate_stage(&gate, 0) == 0);
    assert(armada_modem_boot_gate_ack_publication(&gate, 0) == 0);
    armada_modem_boot_gate_reset(&gate);
    assert(armada_modem_boot_gate_request_start(&gate) == -EAGAIN);
    puts("PASS reset revokes simulated readiness");
}
static void invalid_calls(void)
{
    assert(armada_modem_boot_gate_request_start(NULL) == -EINVAL);
    assert(armada_modem_boot_gate_stage(NULL, 0) == -EINVAL);
    assert(armada_modem_boot_gate_ack_publication(NULL, 0) == -EINVAL);
    armada_modem_boot_gate_reset(NULL);
    puts("PASS NULL gate arguments rejected safely");
}
int main(void)
{
    initial_start_denied();
    deferred_still_denied();
    retry_after_defer();
    acknowledgement_requires_stage();
    explicit_ack_allows_simulation();
    permanent_stage_failure();
    failed_publish();
    reset_revokes_readiness();
    invalid_calls();
    return 0;
}
