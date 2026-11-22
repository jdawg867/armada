/* SPDX-License-Identifier: GPL-2.0 */
/* HOST MOCK ONLY: simulates Linux ERR_PTR encoding, not a real kernel header. */
#ifndef MOCK_LINUX_ERR_H
#define MOCK_LINUX_ERR_H
#include <stdint.h>
#define MAX_ERRNO 4095
#define ERR_PTR(error) ((void *)(intptr_t)(error))
#define IS_ERR(ptr) ((uintptr_t)(ptr) >= (uintptr_t)-MAX_ERRNO)
#define PTR_ERR(ptr) ((long)(intptr_t)(ptr))
#endif
