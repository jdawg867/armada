/* Host mock only; signatures match pinned Linux 7.2.6 smem.h. */
#ifndef ARMADA_MOCK_LINUX_QCOM_SMEM_H
#define ARMADA_MOCK_LINUX_QCOM_SMEM_H
#include <stddef.h>
#define QCOM_SMEM_HOST_ANY -1
int qcom_smem_alloc(unsigned host, unsigned item, size_t size);
void *qcom_smem_get(unsigned host, unsigned item, size_t *size);
#endif
