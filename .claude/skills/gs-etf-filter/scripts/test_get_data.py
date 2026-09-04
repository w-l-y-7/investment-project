# -*- coding: utf-8 -*-
"""单元测试：gs-etf-filter 的 get_data.py 里可离线验证的纯解析逻辑。

只测不联网的函数（rename_fields / parse_professional_result /
parse_custom_result / is_professional_list_mode），绝不调用 call_api 等联网接口。
"""
import contextlib
import io
import unittest
from types import SimpleNamespace

import get_data as g


def _quiet():
    return contextlib.redirect_stdout(io.StringIO())


class TestRenameFields(unittest.TestCase):
    def test_maps_known_field_and_keeps_unknown(self):
        with _quiet():
            out = g.rename_fields({"ofcode": "1", "ofname": "A", "nowrange": "1.2", "x": "y"},
                                  g.FIELD_MAP_4618)
        self.assertEqual(out["产品代码"], "1")
        self.assertEqual(out["产品名称"], "A")
        self.assertEqual(out["实时涨跌"], "1.2")
        self.assertEqual(out["x"], "y")

    def test_empty_dict(self):
        with _quiet():
            self.assertEqual(g.rename_fields({}, g.FIELD_MAP_4620), {})


class TestParseProfessionalResult(unittest.TestCase):
    def test_normal(self):
        data = {"data": [{"listName": "N", "listDes": "D", "listLabel": "L", "listprofit": "5",
                          "profitType": "p",
                          "list": [{"ofcode": "1", "ofname": "A", "nowrange": "1.2"}]}]}
        with _quiet():
            results, info = g.parse_professional_result(data)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["产品代码"], "1")
        self.assertEqual(results[0]["产品名称"], "A")
        self.assertEqual(results[0]["实时涨跌"], "1.2")
        self.assertEqual(info["榜单名称"], "N")
        self.assertEqual(info["榜单平均收益"], "5")

    def test_empty_and_no_data_field(self):
        with _quiet():
            self.assertEqual(g.parse_professional_result({}), ([], {}))
            self.assertEqual(g.parse_professional_result({"data": []}), ([], {}))

    def test_truncates_over_max(self):
        big = {"data": [{"listName": "X", "list": [{"ofcode": str(i)} for i in range(105)]}]}
        with _quiet():
            results, _ = g.parse_professional_result(big)
        self.assertEqual(len(results), g.MAX_RESULTS)


class TestParseCustomResult(unittest.TestCase):
    def test_normal_with_total(self):
        data = {"data": [{"ofcode": "1", "ofname": "B"}], "data1": [{"etfNum": "12"}]}
        with _quiet():
            results, info = g.parse_custom_result(data)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["产品代码"], "1")
        self.assertEqual(results[0]["产品名称"], "B")
        self.assertEqual(info, {"总记录数": "12"})

    def test_no_data1_means_empty_info(self):
        with _quiet():
            results, info = g.parse_custom_result({"data": [{"ofcode": "1"}]})
        self.assertEqual(len(results), 1)
        self.assertEqual(info, {})

    def test_data_not_a_list_returns_no_results(self):
        with _quiet():
            self.assertEqual(g.parse_custom_result({"data": {}}), ([], {}))
            self.assertEqual(g.parse_custom_result({}), ([], {}))


class TestIsProfessionalListMode(unittest.TestCase):
    def test_known_pair_true(self):
        self.assertTrue(g.is_professional_list_mode(
            SimpleNamespace(class_id=2, list_id=21)))

    def test_unknown_pair_false(self):
        self.assertFalse(g.is_professional_list_mode(
            SimpleNamespace(class_id=2, list_id=99)))

    def test_missing_class_false(self):
        self.assertFalse(g.is_professional_list_mode(
            SimpleNamespace(class_id=None, list_id=21)))


if __name__ == "__main__":
    unittest.main()
