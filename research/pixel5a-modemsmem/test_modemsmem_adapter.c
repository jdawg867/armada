/* SPDX-License-Identifier: GPL-2.0 */
#include <assert.h>
#include <errno.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include "modemsmem_adapter.h"

struct mock {
    unsigned char soc[68];
    unsigned char vendor[64];
    int read_error, alloc_error, inspect_error;
    size_t soc_size, vendor_size;
    unsigned reads, allocs, inspects, writes;
};

static void le32(unsigned char *p, uint32_t v)
{
    p[0] = (unsigned char)v;
    p[1] = (unsigned char)(v >> 8);
    p[2] = (unsigned char)(v >> 16);
    p[3] = (unsigned char)(v >> 24);
}
static void setup(struct mock *m)
{
    memset(m, 0, sizeof(*m));
    memset(m->vendor, 0x7e, sizeof(m->vendor));
    m->soc_size = sizeof(m->soc);
    m->vendor_size = sizeof(m->vendor);
    le32(m->soc, 6); /* SOCINFO_VERSION(0, 6) */
    le32(m->soc + 52, 42); /* hw_plat */
    le32(m->soc + 56, 0x00340056); /* plat_ver */
    le32(m->soc + 64, 9); /* hw_plat_subtype */
}
static int read_cb(void *ctx, unsigned host, unsigned item,
                   const unsigned char **data, size_t *size)
{
    struct mock *m = ctx;
    assert(host == (unsigned)-1 && item == 137);
    m->reads++;
    if (m->read_error) return m->read_error;
    *data = m->soc;
    *size = m->soc_size;
    return 0;
}
static int alloc_cb(void *ctx, unsigned host, unsigned item, size_t size)
{
    struct mock *m = ctx;
    assert(host == (unsigned)-1 && item == 134 && size == 64);
    m->allocs++;
    return m->alloc_error;
}
static int inspect_cb(void *ctx, unsigned host, unsigned item,
                      const void **data, size_t *size)
{
    struct mock *m = ctx;
    assert(host == (unsigned)-1 && item == 134);
    m->inspects++;
    if (m->inspect_error) return m->inspect_error;
    *data = m->vendor;
    *size = m->vendor_size;
    return 0;
}
static struct armada_modemsmem_ops ops_for(struct mock *m)
{
    struct armada_modemsmem_ops ops = {
        .read_item = read_cb,
        .alloc_item = alloc_cb,
        .inspect_item = inspect_cb,
        .context = m
    };
    return ops;
}
static void assert_untouched(struct mock *m, const struct armada_modemsmem_payload *out)
{
    const unsigned char *ptr = (const unsigned char *)out;
    for (size_t i = 0; i < sizeof(*out); ++i) assert(ptr[i] == 0xa5);
    for (size_t i = 0; i < sizeof(m->vendor); ++i) assert(m->vendor[i] == 0x7e);
    assert(m->writes == 0);
}
static void test_success(void)
{
    struct mock m; setup(&m);
    struct armada_modemsmem_ops ops = ops_for(&m);
    struct armada_modemsmem_payload p = {0};
    assert(armada_modemsmem_stage(&ops, &p) == 0);
    assert(p.platform == 42 && p.subtype == 9);
    assert(p.major_id == 0x34 && p.minor_id == 0x56);
    assert(p.ftm_magic == 0 && p.dsds_magic == 0 && p.modem_flag == 0);
    assert(m.reads == 1 && m.allocs == 1 && m.inspects == 1);
    for (size_t i=0;i<sizeof(m.vendor);i++) assert(m.vendor[i] == 0x7e);
    puts("PASS stage creates payload without publishing SMEM");
}
static void test_existing_item(void)
{
    struct mock m; setup(&m); m.alloc_error = -EEXIST;
    struct armada_modemsmem_ops ops = ops_for(&m);
    struct armada_modemsmem_payload p = {0};
    assert(armada_modemsmem_stage(&ops, &p) == 0);
    assert(m.inspects == 1 && p.platform == 42);
    puts("PASS existing vendor SMEM is inspected but not overwritten");
}
static void test_read_failure(void)
{
    struct mock m; setup(&m); m.read_error = -EAGAIN;
    struct armada_modemsmem_ops ops = ops_for(&m);
    struct armada_modemsmem_payload p; memset(&p, 0xa5, sizeof(p));
    assert(armada_modemsmem_stage(&ops, &p) == -EAGAIN);
    assert(m.allocs == 0 && m.inspects == 0);
    assert_untouched(&m, &p);
    puts("PASS deferred source read preserves output");
}
static void test_short_socinfo(void)
{
    struct mock m; setup(&m); m.soc_size = 67;
    struct armada_modemsmem_ops ops = ops_for(&m);
    struct armada_modemsmem_payload p; memset(&p, 0xa5, sizeof(p));
    assert(armada_modemsmem_stage(&ops, &p) == -EMSGSIZE);
    assert(m.allocs == 0);
    assert_untouched(&m, &p);
    puts("PASS truncated SoCinfo rejected before allocation");
}
static void test_unknown_format(void)
{
    struct mock m; setup(&m); le32(m.soc, 5);
    struct armada_modemsmem_ops ops = ops_for(&m);
    struct armada_modemsmem_payload p; memset(&p, 0xa5, sizeof(p));
    assert(armada_modemsmem_stage(&ops, &p) == -EOPNOTSUPP);
    assert(m.allocs == 0);
    assert_untouched(&m, &p);
    puts("PASS unreviewed SoCinfo format rejected");
}
static void test_alloc_failure(void)
{
    struct mock m; setup(&m); m.alloc_error = -ENOMEM;
    struct armada_modemsmem_ops ops = ops_for(&m);
    struct armada_modemsmem_payload p; memset(&p, 0xa5, sizeof(p));
    assert(armada_modemsmem_stage(&ops, &p) == -ENOMEM);
    assert(m.inspects == 0);
    assert_untouched(&m, &p);
    puts("PASS allocation error propagated");
}
static void test_bad_vendor_size(void)
{
    struct mock m; setup(&m); m.vendor_size = 63;
    struct armada_modemsmem_ops ops = ops_for(&m);
    struct armada_modemsmem_payload p; memset(&p, 0xa5, sizeof(p));
    assert(armada_modemsmem_stage(&ops, &p) == -EMSGSIZE);
    assert_untouched(&m, &p);
    puts("PASS mismatched vendor SMEM item rejected");
}
static void test_inspect_failure(void)
{
    struct mock m; setup(&m); m.inspect_error = -EIO;
    struct armada_modemsmem_ops ops = ops_for(&m);
    struct armada_modemsmem_payload p; memset(&p, 0xa5, sizeof(p));
    assert(armada_modemsmem_stage(&ops, &p) == -EIO);
    assert_untouched(&m, &p);
    puts("PASS vendor SMEM inspect error propagated");
}
static void test_null_ops(void)
{
    struct mock m; setup(&m);
    struct armada_modemsmem_payload p; memset(&p, 0xa5, sizeof(p));
    struct armada_modemsmem_ops ops = ops_for(&m);
    assert(armada_modemsmem_stage(NULL, &p) == -EINVAL);
    assert(armada_modemsmem_stage(&ops, NULL) == -EINVAL);
    ops.inspect_item = NULL;
    assert(armada_modemsmem_stage(&ops, &p) == -EINVAL);
    assert_untouched(&m, &p);
    puts("PASS incomplete adapter callbacks rejected");
}
int main(void)
{
    test_success();
    test_existing_item();
    test_read_failure();
    test_short_socinfo();
    test_unknown_format();
    test_alloc_failure();
    test_bad_vendor_size();
    test_inspect_failure();
    test_null_ops();
    return 0;
}
