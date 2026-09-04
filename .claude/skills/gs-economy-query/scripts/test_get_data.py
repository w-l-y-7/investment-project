# -*- coding: utf-8 -*-
"""单元测试：gs-economy-query 的 get_data.py。

脚本顶层会在没配 GS_API_KEY 时抛异常，所以测试先塞一个假 key 再 import；
全程不碰真实网络：请求层用 mock 挡住，只验证 SSL 辅助函数与参数拼装逻辑。
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
        # 网络失败时走 curl 备用；这里把 curl 也挡住，验证返回值来自备用路径
        with mock.patch("urllib.request.urlopen",
                        side_effect=urllib_error.URLError("boom")), \
             mock.patch.object(g, "_curl_request", return_value={"error": "curl-failed"}):
            out = g._make_request("https://example.com/x", {"a": "1"})
        self.assertEqual(out, {"error": "curl-failed"})


class TestQueryMacroDataParams(unittest.TestCase):
    def test_builds_url_and_params(self):
        with mock.patch.object(g, "_make_request", return_value={"content": "ok"}) as mk:
            result = g.query_macro_data("查询人口")
        url, params = mk.call_args[0]
        self.assertEqual(result, {"content": "ok"})
        self.assertTrue(url.endswith("/agent/adapter/query"))
        self.assertEqual(params["text"], "查询人口")
        self.assertEqual(params["softName"], g.SOFT_NAME)
        self.assertEqual(params["apiKey"], "unit-test-dummy-key")


if __name__ == "__main__":
    unittest.main()
