# -*- coding: utf-8 -*-
"""单元测试：gs-smart-stock-picking 的 gs_stock_picking.py。

只测不联网的 print_result（结果打印/分支逻辑），绝不调用
smart_stock_picking（它会真的连国信证券接口）。
"""
import contextlib
import io
import unittest

import gs_stock_picking as g


def run(result):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        g.print_result(result)
    return buf.getvalue()


class TestPrintResult(unittest.TestCase):
    def test_none_prints_no_result(self):
        self.assertEqual(run(None), "未获取到结果\n")

    def test_result_without_result_key(self):
        self.assertEqual(run({"foo": 1}), "返回数据格式异常\n")

    def test_result_list_empty(self):
        self.assertEqual(run({"result": []}), "返回数据格式异常\n")

    def test_error_code_prints_failure(self):
        out = run({"result": [{"code": -1, "msg": "参数错误"}]})
        self.assertIn("状态码: -1", out)
        self.assertIn("消息: 参数错误", out)
        self.assertIn("查询失败", out)

    def test_success_data_prints_table(self):
        data = {"result": [{"code": 0, "msg": "ok"}],
                "data": [{"table": {"产品代码": ["600519"]}}]}
        out = run(data)
        self.assertIn("状态码: 0", out)
        self.assertIn("结果 #1:", out)
        self.assertIn("产品代码:", out)
        self.assertIn("  - 600519", out)

    def test_success_without_data(self):
        out = run({"result": [{"code": 0, "msg": "ok"}]})
        self.assertIn("状态码: 0", out)
        self.assertNotIn("查询失败", out)

    def test_data_not_list_flags_bad_format(self):
        out = run({"result": [{"code": 0, "msg": "ok"}], "data": {"x": 1}})
        self.assertIn("返回数据格式异常", out)


if __name__ == "__main__":
    unittest.main()
