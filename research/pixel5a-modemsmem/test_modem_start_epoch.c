/* SPDX-License-Identifier: GPL-2.0 */
#include <assert.h>
#include <errno.h>
#include <stdint.h>
#include <stdio.h>
#include "modem_start_epoch.h"

static struct armada_modem_start_epoch new_gate(void)
{
    struct armada_modem_start_epoch g;
    armada_start_epoch_init(&g);
    return g;
}
static void assert_denied_all(const struct armada_modem_start_epoch *g, int expected)
{
    assert(armada_start_epoch_can_start(g, ARMADA_START_AUTOMATIC) == expected);
    assert(armada_start_epoch_can_start(g, ARMADA_START_EXPLICIT) == expected);
    assert(armada_start_epoch_can_start(g, ARMADA_START_RECOVERY) == expected);
}
static void initial_denial(void)
{
    struct armada_modem_start_epoch g = new_gate();
    assert_denied_all(&g, -EAGAIN);
    puts("PASS automatic, explicit and recovery starts denied initially");
}
static void staged_only_denied(void)
{
    struct armada_modem_start_epoch g = new_gate();
    assert(armada_start_epoch_stage(&g, 1, 0) == 0);
    assert_denied_all(&g, -EAGAIN);
    puts("PASS staging cannot authorize any start origin");
}
static void deferred_then_ready(void)
{
    struct armada_modem_start_epoch g = new_gate();
    assert(armada_start_epoch_stage(&g, 1, -EAGAIN) == -EAGAIN);
    assert_denied_all(&g, -EAGAIN);
    assert(armada_start_epoch_stage(&g, 1, 0) == 0);
    assert(armada_start_epoch_ack(&g, 1, 0) == 0);
    assert_denied_all(&g, 0);
    puts("PASS simulated defer then acknowledgement enables all origins");
}
static void premature_ack_denied(void)
{
    struct armada_modem_start_epoch g = new_gate();
    assert(armada_start_epoch_ack(&g, 1, 0) == -EAGAIN);
    assert_denied_all(&g, -EAGAIN);
    puts("PASS ack cannot precede staging");
}
static void restart_revokes(void)
{
    struct armada_modem_start_epoch g = new_gate();
    uint64_t epoch = 0;
    assert(armada_start_epoch_stage(&g, 1, 0) == 0);
    assert(armada_start_epoch_ack(&g, 1, 0) == 0);
    assert_denied_all(&g, 0);
    assert(armada_start_epoch_restart(&g, &epoch) == 0 && epoch == 2);
    assert_denied_all(&g, -EAGAIN);
    puts("PASS restart revokes all start permissions");
}
static void stale_ack_rejected(void)
{
    struct armada_modem_start_epoch g = new_gate();
    uint64_t epoch = 0;
    assert(armada_start_epoch_stage(&g, 1, 0) == 0);
    assert(armada_start_epoch_restart(&g, &epoch) == 0);
    assert(armada_start_epoch_ack(&g, 1, 0) == -ESTALE);
    assert_denied_all(&g, -EAGAIN);
    puts("PASS stale generation acknowledgement rejected");
}
static void current_epoch_required(void)
{
    struct armada_modem_start_epoch g = new_gate();
    uint64_t epoch = 0;
    assert(armada_start_epoch_restart(&g, &epoch) == 0);
    assert(armada_start_epoch_stage(&g, 1, 0) == -ESTALE);
    assert(armada_start_epoch_ack(&g, epoch, 0) == -EAGAIN);
    assert(armada_start_epoch_stage(&g, epoch, 0) == 0);
    assert(armada_start_epoch_ack(&g, epoch, 0) == 0);
    assert_denied_all(&g, 0);
    puts("PASS only current generation staging and acknowledgement accepted");
}
static void permanent_failure_denied(void)
{
    struct armada_modem_start_epoch g = new_gate();
    assert(armada_start_epoch_stage(&g, 1, -EIO) == -EIO);
    assert(armada_start_epoch_stage(&g, 1, 0) == -EIO);
    assert_denied_all(&g, -EIO);
    puts("PASS permanent stage failure denies all start origins");
}
static void failed_ack_denied(void)
{
    struct armada_modem_start_epoch g = new_gate();
    assert(armada_start_epoch_stage(&g, 1, 0) == 0);
    assert(armada_start_epoch_ack(&g, 1, -EIO) == -EIO);
    assert_denied_all(&g, -EIO);
    puts("PASS failed publication denies all start origins");
}
static void repeat_staging_revokes_ack(void)
{
    struct armada_modem_start_epoch g = new_gate();
    assert(armada_start_epoch_stage(&g, 1, 0) == 0);
    assert(armada_start_epoch_ack(&g, 1, 0) == 0);
    assert(armada_start_epoch_stage(&g, 1, 0) == 0);
    assert_denied_all(&g, -EAGAIN);
    puts("PASS repeated staging revokes prior acknowledgement");
}
static void invalid_origin_and_null(void)
{
    struct armada_modem_start_epoch g = new_gate();
    assert(armada_start_epoch_can_start(NULL, ARMADA_START_AUTOMATIC) == -EINVAL);
    assert(armada_start_epoch_can_start(&g, (enum armada_start_origin)99) == -EINVAL);
    assert(armada_start_epoch_stage(NULL, 1, 0) == -EINVAL);
    assert(armada_start_epoch_ack(NULL, 1, 0) == -EINVAL);
    assert(armada_start_epoch_restart(NULL, NULL) == -EINVAL);
    puts("PASS invalid origin and NULL gate rejected");
}
static void overflow_prevents_wrap(void)
{
    struct armada_modem_start_epoch g = new_gate();
    uint64_t epoch = 0;
    g.epoch = UINT64_MAX;
    assert(armada_start_epoch_restart(&g, &epoch) == -EOVERFLOW);
    assert(g.epoch == UINT64_MAX);
    puts("PASS generation wrap refused");
}
int main(void)
{
    initial_denial(); staged_only_denied(); deferred_then_ready();
    premature_ack_denied(); restart_revokes(); stale_ack_rejected();
    current_epoch_required(); permanent_failure_denied(); failed_ack_denied();
    repeat_staging_revokes_ack(); invalid_origin_and_null(); overflow_prevents_wrap();
    return 0;
}
