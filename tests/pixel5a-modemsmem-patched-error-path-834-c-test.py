#!/usr/bin/env python3
"""Step 834: compile and execute the reviewed C error-return block, host-only.

Uses EXACT Step 833 replacement text, not a separately reimplemented C branch.
Cannot prove compilation of the full kernel driver, modem probe, or telephony.
"""
import importlib.util
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
VERIFIER=ROOT/"tests/pixel5a-modemsmem-full-pinned-source-patch-833-test.py"
spec=importlib.util.spec_from_file_location("armada_step833",VERIFIER)
verifier=importlib.util.module_from_spec(spec)
spec.loader.exec_module(verifier)

HEADER=r"""
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#define EPROBE_DEFER 517
#define EEXIST 17
#define ENOMEM 12
#define EINVAL 22
#define QCOM_SMEM_HOST_ANY (~0U)
#define SMEM_ID_VENDOR0 134
struct modem_smem_type { unsigned version; };
static struct modem_smem_type sample;
static int mock_get_error;
static int mock_wrong_size;
static int log_count;
static void *dev;
static void dev_err(void *device,const char *msg) {
 (void)device; (void)msg; ++log_count;
}
static struct modem_smem_type *qcom_smem_get(unsigned host,unsigned item,size_t *size) {
 (void)host; (void)item;
 *size=sizeof(sample) + (mock_wrong_size ? 4 : 0);
 if (mock_get_error) return (struct modem_smem_type *)(intptr_t)mock_get_error;
 return &sample;
}
#define IS_ERR(p) ((uintptr_t)(void *)(p) >= (uintptr_t)-4095)
#define PTR_ERR(p) ((long)(intptr_t)(p))
static int exercise(int alloc_result,int get_error,int wrong_size) {
 int ret=alloc_result;
 size_t size=0;
 struct modem_smem_type *modem_smem;
 mock_get_error=get_error;
 mock_wrong_size=wrong_size;
 log_count=0;
"""
FOOTER=r"""
 (void)modem_smem;
 return 0;
}
static int checks;
static void expect(const char *name,int got,int want) {
 if(got!=want){fprintf(stderr,"FAIL %s got=%d want=%d\n",name,got,want);checks=-999;return;}
 if(checks>=0)++checks;
}
int main(void) {
 expect("alloc_defer",exercise(-EPROBE_DEFER,0,0),-EPROBE_DEFER);
 expect("alloc_eexist",exercise(-EEXIST,0,0),0);
 expect("alloc_success",exercise(0,0,0),0);
 expect("alloc_nomem",exercise(-ENOMEM,0,0),-ENOMEM);
 expect("alloc_other",exercise(-EINVAL,0,0),-ENOMEM);
 expect("get_defer",exercise(0,-EPROBE_DEFER,0),-EPROBE_DEFER);
 expect("get_other",exercise(0,-EINVAL,0),-ENOMEM);
 expect("get_nomem",exercise(0,-ENOMEM,0),-ENOMEM);
 expect("size_mismatch",exercise(0,0,1),-ENOMEM);
 expect("size_match",exercise(0,0,0),0);
 if(checks!=10){fprintf(stderr,"FAIL expected 10, got %d\n",checks);return 1;}
 puts("PASS 10 host-only compiled error mapping cases");
 return 0;
}
"""

class CompiledErrorMapping(unittest.TestCase):
    def test_compiled_exact_replacement_error_paths(self):
        replacement=verifier.REPLACEMENT
        # Compile the reviewed, source-derived C branch with minimal stand-in
        # definitions, not an independent reimplementation of its conditions.
        self.assertIn("if (ret == -EPROBE_DEFER)",replacement)
        self.assertIn("PTR_ERR(modem_smem)",replacement)
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            c=root/"modemsmem_error_block.c"
            executable=root/"modemsmem_error_block"
            c.write_text(HEADER+replacement+FOOTER,encoding="utf-8")
            compile_result=subprocess.run(
                ["cc","-std=c11","-Wall","-Wextra","-Werror","-pedantic","-O1",
                 "-fsanitize=undefined","-fno-omit-frame-pointer",
                 str(c),"-o",str(executable)],
                capture_output=True,text=True)
            self.assertEqual(compile_result.returncode,0,compile_result.stderr)
            run=subprocess.run([str(executable)],capture_output=True,text=True)
            self.assertEqual(run.returncode,0,run.stderr)
            self.assertIn("PASS 10 host-only compiled error mapping cases",run.stdout)

if __name__=="__main__":
    unittest.main()
