# -*- coding: utf-8 -*-
"""单元测试：gs-stock-market-query 的 get_data.py。

脚本顶层会在没配 GS_API_KEY 时抛异常，所以测试先塞一个假 key 再 import；
全程不碰真实网络：只验证 SSL 辅助、请求兜底路径，以及各行情查询函数拼出的 URL/参数。
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

    def test_single_hq(self):
        url, params = self._capture(g.query_single_hq, "600519", 0, 0)
        self.assertTrue(url.endswith("/queryHQInfo/1.0"))
        self.assertEqual(params["code"], "600519")
        self.assertEqual(params["setCode"], 0)
        self.assertEqual(params["target"], 0)

    def test_comb_hq_joins_lists(self):
        url, params = self._capture(g.query_comb_hq, ["600519", "000001"], [1, 0])
        self.assertTrue(url.endswith("/queryCombHQ/1.0"))
        self.assertEqual(params["code"], "600519,000001")
        self.assertEqual(params["setCode"], "1,0")

    def test_fund_flow_converts_to_string(self):
        url, params = self._capture(g.query_fund_flow, "600519", 1, 30)
        self.assertTrue(url.endswith("/queryFundFlow/1.0"))
        self.assertEqual(params["period"], "30")
        self.assertEqual(params["setCode"], "1")

    def test_multi_hq_uses_api_field_names(self):
        url, params = self._capture(g.query_multi_hq, 6, 10, 1, 0)
        self.assertTrue(url.endswith("/queryMultiHQ/1.0"))
        self.assertEqual(params["setDomain"], 6)
        self.assertEqual(params["wantNum"], 10)
        self.assertEqual(params["sortType"], 1)

    def test_past_hq_mas_optional(self):
        _, p1 = self._capture(g.query_past_hq, "600519", 0, 20)
        self.assertNotIn("mas", p1)
        _, p2 = self._capture(g.query_past_hq, "600519", 0, 20, 0, "5,10")
        self.assertEqual(p2["mas"], "5,10")


if __name__ == "__main__":
    unittest.main()
