# -*- coding: utf-8 -*-
"""单元测试：security-audit 的 security_scan.py（安全可疑点扫描逻辑）。"""
import os
import shutil
import tempfile
import unittest
from pathlib import Path

import security_scan as ss


class TestPlaceholder(unittest.TestCase):
    def test_true_placeholders(self):
        for v in ("your_password", "examplekey", "sample_password", "changeme", "<secret>", "TODO key"):
            self.assertTrue(ss._looks_like_placeholder(v), v)

    def test_real_values(self):
        for v in ("s3cr3tpass", "abc12345", "a1b2c3d4e5"):
            self.assertFalse(ss._looks_like_placeholder(v), v)


class TestScanFile(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp)

    def _write(self, rel, content):
        p = Path(self.tmp) / rel
        p.write_text(content, encoding="utf-8")
        return p

    def test_hardcoded_password_and_eval(self):
        p = self._write("app.py", 'password = "s3cr3tpass"\nresult = eval("1+1")\n')
        findings, param_safe, unreadable = ss.scan_file(p)
        self.assertFalse(unreadable)
        self.assertEqual(param_safe, 0)
        self.assertEqual(len(findings), 2)
        self.assertEqual(findings[0][0], 1)
        self.assertEqual(findings[0][1], "高危")
        self.assertEqual(findings[1][1], "高危")

    def test_env_file_password_is_info_not_high(self):
        p = self._write(".env", 'PASSWORD = "abc12345"\n')
        findings, _, _ = ss.scan_file(p)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0][1], "提示")

    def test_private_key_aws_url_verify_and_sql_concat(self):
        p = self._write(
            "secret.py",
            "-----BEGIN RSA PRIVATE KEY-----\n"
            'key = "AKIAABCDEFGHIJKLMNOP"\n'
            'db = "mysql://root:secret@localhost/x"\n'
            "verify = False\n"
            'sql = "SELECT * FROM t WHERE id = " + user_input\n'
            'sql2 = "SELECT * FROM t WHERE id = ?"\n',
        )
        findings, param_safe, unreadable = ss.scan_file(p)
        self.assertFalse(unreadable)
        # ? 参数占位的 sql2 被记成安全写法
        self.assertEqual(param_safe, 1)
        levels = [lv for _, lv, _ in findings]
        # 私钥、AWS、连接串带密码、SQL 拼接 = 4 个高危；verify=False = 1 个中危
        self.assertEqual(levels.count("高危"), 4)
        self.assertEqual(levels.count("中危"), 1)
        # 第 5 行应该是 SQL 注入风险提示
        line5 = [f for f in findings if f[0] == 5]
        self.assertEqual(len(line5), 1)
        self.assertIn("拼接", line5[0][2])

    def test_fstring_sql_flags_injection(self):
        p = self._write("q.py", 'query = f"SELECT * FROM t WHERE id = {user_id}"\n')
        findings, _, _ = ss.scan_file(p)
        self.assertEqual(len(findings), 1)
        self.assertIn("f-string", findings[0][2])

    def test_clean_code_no_findings(self):
        p = self._write(
            "clean.py",
            "import os\n"
            "def add(a, b):\n"
            "    return a + b\n"
            "print(add(1, 2))\n",
        )
        findings, param_safe, unreadable = ss.scan_file(p)
        self.assertFalse(unreadable)
        self.assertEqual(findings, [])
        self.assertEqual(param_safe, 0)

    def test_unreadable_file(self):
        findings, param_safe, unreadable = ss.scan_file(Path(self.tmp) / "ghost.py")
        self.assertTrue(unreadable)
        self.assertEqual(findings, [])
        self.assertEqual(param_safe, 0)


class TestCollect(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp)

    def _touch(self, rel):
        p = Path(self.tmp) / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("", encoding="utf-8")
        return p

    def test_directory_collects_code_and_config(self):
        self._touch("a.py")
        self._touch("b.txt")
        self._touch("c.js")
        self._touch(".env")
        self._touch("d.pem")
        self._touch("__pycache__/z.py")
        self._touch(".git/secret.py")
        names = sorted(p.name for p in ss.collect([self.tmp]))
        self.assertEqual(names, [".env", "a.py", "c.js", "d.pem"])

    def test_single_file_in_allowed_ext(self):
        p = self._touch("a.py")
        got = ss.collect([p])
        self.assertEqual([str(x) for x in got], [str(p)])

    def test_single_file_not_in_allowed_ext(self):
        p = self._touch("b.txt")
        self.assertEqual(ss.collect([p]), [])

    def test_missing_path(self):
        self.assertEqual(ss.collect([Path(self.tmp) / "nope"]), [])


if __name__ == "__main__":
    unittest.main()
