/* SPDX-License-Identifier: GPL-2.0 */
#include <assert.h>
#include <stddef.h>
#include <stdio.h>
#include <stdint.h>
#include "kernel_smem_facade.h"

static void *get_value;
static size_t get_size;
static int alloc_value;
static unsigned get_calls, alloc_calls;

void *qcom_smem_get(unsigned host, unsigned item, size_t *size)
{
    assert(host == (unsigned)-1 && item == 137);
    get_calls++;
    *size = get_size;
    return get_value;
}
int qcom_smem_alloc(unsigned host, unsigned item, size_t size)
{
    assert(host == (unsigned)-1 && item == 134 && size == 64);
    alloc_calls++;
    return alloc_value;
}
static void success(void)
{
    char memory[68] = {0};
    const void *ptr = NULL;
    size_t size = 0;
    get_value = memory;
    get_size = sizeof(memory);
    assert(armada_modemsmem_kernel_get(137, &ptr, &size) == 0);
    assert(ptr == memory && size == sizeof(memory) && get_calls == 1);
    puts("PASS get returns validated nonerror pointer and size");
}
static void deferred(void)
{
    const void *ptr = (void *)0x1;
    size_t size = 999;
    get_value = ERR_PTR(-EPROBE_DEFER);
    assert(armada_modemsmem_kernel_get(137, &ptr, &size) == -EPROBE_DEFER);
    assert(ptr == (void *)0x1 && size == 999);
    puts("PASS ERR_PTR defer propagated without dereference or output mutation");
}
static void missing(void)
{
    const void *ptr = (void *)0x1;
    size_t size = 999;
    get_value = ERR_PTR(-ENOENT);
    assert(armada_modemsmem_kernel_get(137, &ptr, &size) == -ENOENT);
    assert(ptr == (void *)0x1 && size == 999);
    puts("PASS ERR_PTR missing item propagated");
}
static void not_initialized(void)
{
    const void *ptr = (void *)0x1;
    size_t size = 999;
    get_value = ERR_PTR(-ENODEV);
    assert(armada_modemsmem_kernel_get(137, &ptr, &size) == -ENODEV);
    assert(ptr == (void *)0x1 && size == 999);
    puts("PASS ERR_PTR uninitialized SMEM propagated");
}
static void null_pointer(void)
{
    const void *ptr = (void *)0x1;
    size_t size = 999;
    get_value = NULL;
    assert(armada_modemsmem_kernel_get(137, &ptr, &size) == -ENODATA);
    assert(ptr == (void *)0x1 && size == 999);
    puts("PASS unexpected null pointer rejected");
}
static void null_arguments(void)
{
    size_t size = 0;
    const void *ptr = NULL;
    unsigned before = get_calls;
    assert(armada_modemsmem_kernel_get(137, NULL, &size) == -EINVAL);
    assert(armada_modemsmem_kernel_get(137, &ptr, NULL) == -EINVAL);
    assert(before == get_calls);
    puts("PASS invalid output arguments rejected before SMEM call");
}
static void allocation_integer_errors(void)
{
    alloc_value = -EPROBE_DEFER;
    assert(armada_modemsmem_kernel_alloc(134, 64) == -EPROBE_DEFER);
    alloc_value = -EEXIST;
    assert(armada_modemsmem_kernel_alloc(134, 64) == -EEXIST);
    alloc_value = 0;
    assert(armada_modemsmem_kernel_alloc(134, 64) == 0);
    assert(alloc_calls == 3);
    puts("PASS allocation keeps integer errors including EEXIST");
}
int main(void)
{
    success(); deferred(); missing(); not_initialized();
    null_pointer(); null_arguments(); allocation_integer_errors();
    return 0;
}
