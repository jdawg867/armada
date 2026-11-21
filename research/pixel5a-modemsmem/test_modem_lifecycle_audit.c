/* SPDX-License-Identifier: GPL-2.0 */
#include <assert.h>
#include <errno.h>
#include <stdint.h>
#include <stdio.h>
#include "modem_lifecycle_audit.h"

static void ready(struct armada_modem_lifecycle_audit *ctx)
{
    armada_lifecycle_init(ctx);
    assert(armada_lifecycle_stage(ctx, 1, 0) == 0);
    assert(armada_lifecycle_ack(ctx, 1, 0) == 0);
    assert(armada_lifecycle_start(ctx, ARMADA_START_AUTOMATIC) == 0);
}
static void crash_revokes_all_paths(void)
{
    struct armada_modem_lifecycle_audit ctx;
    uint64_t next = 0;
    ready(&ctx);
    assert(armada_lifecycle_crash(&ctx, &next) == 0 && next == 2);
    for (int origin = ARMADA_START_AUTOMATIC; origin <= ARMADA_START_RECOVERY; origin++)
        assert(armada_lifecycle_start(&ctx, (enum armada_start_origin)origin) == -EAGAIN);
    puts("PASS crash revokes automatic, explicit and recovery starts");
}
static void delayed_old_ack_rejected(void)
{
    struct armada_modem_lifecycle_audit ctx;
    uint64_t next = 0;
    ready(&ctx);
    assert(armada_lifecycle_crash(&ctx, &next) == 0);
    assert(armada_lifecycle_ack(&ctx, 1, 0) == -ESTALE);
    assert(armada_lifecycle_start(&ctx, ARMADA_START_RECOVERY) == -EAGAIN);
    puts("PASS old async publication acknowledgement cannot revive readiness");
}
static void recovery_requires_new_ack(void)
{
    struct armada_modem_lifecycle_audit ctx;
    uint64_t next = 0;
    ready(&ctx);
    assert(armada_lifecycle_crash(&ctx, &next) == 0);
    assert(armada_lifecycle_resume_from_crash(&ctx) == -EAGAIN);
    assert(armada_lifecycle_stage(&ctx, next, 0) == 0);
    assert(armada_lifecycle_resume_from_crash(&ctx) == -EAGAIN);
    assert(armada_lifecycle_ack(&ctx, next, 0) == 0);
    assert(armada_lifecycle_start(&ctx, ARMADA_START_RECOVERY) == -EAGAIN);
    assert(armada_lifecycle_resume_from_crash(&ctx) == 0);
    assert(armada_lifecycle_start(&ctx, ARMADA_START_RECOVERY) == 0);
    puts("PASS recovered generation needs staging and fresh acknowledgement");
}
static void removal_terminal(void)
{
    struct armada_modem_lifecycle_audit ctx;
    ready(&ctx);
    assert(armada_lifecycle_remove(&ctx) == 0);
    assert(armada_lifecycle_start(&ctx, ARMADA_START_AUTOMATIC) == -ENODEV);
    assert(armada_lifecycle_start(&ctx, ARMADA_START_EXPLICIT) == -ENODEV);
    assert(armada_lifecycle_start(&ctx, ARMADA_START_RECOVERY) == -ENODEV);
    assert(armada_lifecycle_ack(&ctx, 1, 0) == -ENODEV);
    assert(armada_lifecycle_stage(&ctx, 1, 0) == -ENODEV);
    assert(armada_lifecycle_resume_from_crash(&ctx) == -ENODEV);
    puts("PASS removal rejects starts and late callbacks");
}
static void removal_before_delayed_ack(void)
{
    struct armada_modem_lifecycle_audit ctx;
    armada_lifecycle_init(&ctx);
    assert(armada_lifecycle_stage(&ctx, 1, 0) == 0);
    assert(armada_lifecycle_remove(&ctx) == 0);
    assert(armada_lifecycle_ack(&ctx, 1, 0) == -ENODEV);
    assert(armada_lifecycle_start(&ctx, ARMADA_START_AUTOMATIC) == -ENODEV);
    puts("PASS remove between staging and acknowledgement is fail-closed");
}
static void duplicate_crash_denied(void)
{
    struct armada_modem_lifecycle_audit ctx;
    uint64_t next = 0;
    ready(&ctx);
    assert(armada_lifecycle_crash(&ctx, &next) == 0);
    assert(armada_lifecycle_crash(&ctx, &next) == -EALREADY);
    assert(ctx.gate.epoch == 2);
    puts("PASS duplicate crash does not advance epoch twice");
}
static void failed_recovery_still_blocked(void)
{
    struct armada_modem_lifecycle_audit ctx;
    uint64_t next = 0;
    ready(&ctx);
    assert(armada_lifecycle_crash(&ctx, &next) == 0);
    assert(armada_lifecycle_stage(&ctx, next, -EIO) == -EIO);
    assert(armada_lifecycle_resume_from_crash(&ctx) == -EAGAIN);
    assert(armada_lifecycle_start(&ctx, ARMADA_START_RECOVERY) == -EAGAIN);
    puts("PASS failed recovery stage cannot restart modem");
}
static void epoch_overflow_fail_closed(void)
{
    struct armada_modem_lifecycle_audit ctx;
    uint64_t next = 0;
    ready(&ctx);
    ctx.gate.epoch = UINT64_MAX;
    assert(armada_lifecycle_crash(&ctx, &next) == -EOVERFLOW);
    assert(ctx.gate.epoch == UINT64_MAX);
    assert(armada_lifecycle_start(&ctx, ARMADA_START_EXPLICIT) == -EAGAIN);
    puts("PASS generation overflow rejects crash without authorizing start");
}
static void invalid_inputs(void)
{
    assert(armada_lifecycle_crash(NULL, NULL) == -EINVAL);
    assert(armada_lifecycle_remove(NULL) == -EINVAL);
    assert(armada_lifecycle_ack(NULL, 1, 0) == -EINVAL);
    assert(armada_lifecycle_stage(NULL, 1, 0) == -EINVAL);
    assert(armada_lifecycle_start(NULL, ARMADA_START_AUTOMATIC) == -EINVAL);
    assert(armada_lifecycle_resume_from_crash(NULL) == -EINVAL);
    puts("PASS invalid lifecycle handles rejected");
}
int main(void)
{
    crash_revokes_all_paths(); delayed_old_ack_rejected();
    recovery_requires_new_ack(); removal_terminal();
    removal_before_delayed_ack(); duplicate_crash_denied();
    failed_recovery_still_blocked(); epoch_overflow_fail_closed(); invalid_inputs();
    return 0;
}
