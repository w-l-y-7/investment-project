# -*- coding: utf-8 -*-
"""单元测试：comment-check 的 comment_ratio.py（注释占比统计逻辑）。"""
import os
import shutil
import tempfile
import unittest

import comment_ratio as cr

SAMPLE = '"""模块文档。"""\nimport os\n# 注释行\n\ndef f():\n    """函数文档。"""\n    return 1\n'


def write_tmp(source, suffix=".py"):
    """写一个临时 .py 文件，返回 (路径, 清理函数)。"""
    fd, path = tempfile.mkstemp(suffix=suffix)
    os.close(fd)
    with open(path, "w", encoding="utf-8") as f:
        f.write(source)
    return path


class TestDocstringLines(unittest.TestCase):
    def test_docstring_line_numbers(self):
        # 第 1 行是模块 docstring，第 6 行是函数 docstring
        self.assertEqual(cr._docstring_lines(SAMPLE), {1, 6})

    def test_assignment_string_is_not_docstring(self):
        # 赋值的字符串（x = "abc"）不该被当成文档
        src = 'x = "just a string"\n# comment\nimport os\n'
        self.assertEqual(cr._docstring_lines(src), set())

    def test_broken_source_does_not_raise(self):
        # 解析不了的源码也要兜底，不能抛异常
        self.assertEqual(cr._docstring_lines('def f(:\n    "x\n'), set())


def _safe_unlink(path):
    try:
        os.unlink(path)
    except OSError:
        pass


class TestAnalyze(unittest.TestCase):
    def _analyze(self, source):
        p = write_tmp(source)
        self.addCleanup(_safe_unlink, p)
        return p, cr.analyze(p)

    def test_normal_file_counts(self):
        path, r = self._analyze(SAMPLE)
        self.assertEqual(r["total"], 7)
        self.assertEqual(r["blank"], 1)
        self.assertEqual(r["code"], 3)
        self.assertEqual(r["comment"], 1)
        self.assertEqual(r["docstring"], 2)
        self.assertEqual(r["comment_total"], 3)
        self.assertEqual(r["ratio"], 0.5)
        self.assertTrue(path in r["path"])

    def test_empty_file(self):
        _, r = self._analyze("")
        self.assertEqual(r["total"], 0)
        self.assertEqual(r["code"], 0)
        self.assertEqual(r["comment_total"], 0)
        self.assertEqual(r["ratio"], 0)

    def test_only_blank_and_comments(self):
        _, r = self._analyze("# 1\n# 2\n\n")
        self.assertEqual(r["total"], 3)
        self.assertEqual(r["comment"], 2)
        self.assertEqual(r["blank"], 1)
        self.assertEqual(r["code"], 0)
        self.assertEqual(r["comment_total"], 2)
        self.assertEqual(r["ratio"], 1.0)

    def test_all_code_no_comment(self):
        _, r = self._analyze("x = 1\ny = 2\nprint(x + y)\n")
        self.assertEqual(r["code"], 3)
        self.assertEqual(r["comment_total"], 0)
        self.assertEqual(r["ratio"], 0)


class TestLevel(unittest.TestCase):
    def test_boundaries(self):
        self.assertEqual(cr._level(0.30), "达标")
        self.assertEqual(cr._level(0.50), "达标")
        self.assertEqual(cr._level(0.20), "欠注释")
        self.assertEqual(cr._level(0.15), "欠注释")
        self.assertEqual(cr._level(0.14), "严重缺注释")
        self.assertEqual(cr._level(0.0), "严重缺注释")


class TestCollect(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp)

    def _touch(self, rel):
        p = os.path.join(self.tmp, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        open(p, "w", encoding="utf-8").close()
        return p

    def test_directory_collects_py_and_skips_blacklist(self):
        self._touch("a.py")
        self._touch("b.txt")
        self._touch("sub/c.py")
        self._touch(".claude/hidden.py")
        self._touch("__pycache__/z.py")
        got = [os.path.relpath(str(f), self.tmp) for f in cr.collect([self.tmp])]
        self.assertEqual(sorted(got), sorted(["a.py", os.path.join("sub", "c.py")]))

    def test_single_py_file(self):
        p = self._touch("a.py")
        got = cr.collect([p])
        self.assertEqual([os.path.basename(str(f)) for f in got], ["a.py"])

    def test_non_py_file_ignored(self):
        p = self._touch("a.txt")
        self.assertEqual(cr.collect([p]), [])

    def test_missing_path_ignored(self):
        self.assertEqual(cr.collect([os.path.join(self.tmp, "nope")]), [])


if __name__ == "__main__":
    unittest.main()
