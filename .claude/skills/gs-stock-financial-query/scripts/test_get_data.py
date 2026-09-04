# -*- coding: utf-8 -*-
"""单元测试：gs-stock-financial-query 的 get_data.py。

脚本顶层会在没配 GS_API_KEY 时抛异常，所以测试先塞一个假 key 再 import；
全程不碰真实网络：只验证 SSL 辅助、请求兜底路径，以及各查询函数拼出的 URL/参数。
"""
import os
os.environ["GS_API_KEY"] = "unit-test-dummy-key"

import ssl
import unittest
from unittest import mock
from urllib import error as urllib_error

import get_data as g


class TestCreateSslContext(unittest.TestCase):
    def test_returns_unverified_context(self):
        ctx = g._create_ssl_context()
        self.assertIsNotNone(ctx)
        self.assertEqual(ctx.verify_mode, ssl.CERT_NONE)
        self.assertFalse(ctx.check_hostname)


class TestMakeRequestOffline(unittest.TestCase):
    def test_urlopen_failure_falls_back_to_curl_result(self):
        with mock.patch("urllib.request.urlopen",
                        side_effect=urllib_error.URLError("boom")), \
             mock.patch.object(g, "_curl_request", return_value={"error": "curl-failed"}):
            out = g._make_request("https://example.com/x", {"a": "1"})
        self.assertEqual(out, {"error": "curl-failed"})


class TestQueryParams(unittest.TestCase):
    def _capture(self, fn, *args, **kwargs):
        with mock.patch.object(g, "_make_request", return_value={}) as mk:
            fn(*args, **kwargs)
        url, params = mk.call_args[0]
        return url, params

    def test_a_balance_sheet_defaults(self):
        url, params = self._capture(g.query_a_stock_balance_sheet, "600000", "SH")
        self.assertTrue(url.endswith("/balanceSheet/1.0"))
        self.assertEqual(params["code"], "600000")
        self.assertEqual(params["market"], "SH")
        self.assertEqual(params["reportType"], "Q0")
        self.assertEqual(params["count"], "1")
        self.assertNotIn("reportYear", params)

    def test_a_income_statement_with_year(self):
        url, params = self._capture(g.query_a_stock_income_statement,
                                    "600000", "SH", "Q4", "2024")
        self.assertTrue(url.endswith("/incomeStatement/1.0"))
        self.assertEqual(params["reportYear"], "2024")

    def test_hk_balance_uses_hk_market_and_no_extra(self):
        url, params = self._capture(g.query_hk_stock_balance_sheet, "00700")
        self.assertTrue(url.endswith("/balanceSheet/1.0"))
        self.assertEqual(params["market"], "HK")
        self.assertNotIn("reportYear", params)
        self.assertNotIn("reportType", params)

    def test_hk_cashflow_optional_params(self):
        url, params = self._capture(g.query_hk_stock_cash_flow_statement,
                                    "00700", "2023", "Q4")
        self.assertTrue(url.endswith("/cashFlowStatement/1.0"))
        self.assertEqual(params["reportYear"], "2023")
        self.assertEqual(params["reportType"], "Q4")


if __name__ == "__main__":
    unittest.main()
