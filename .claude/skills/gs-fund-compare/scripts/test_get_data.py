# -*- coding: utf-8 -*-
"""单元测试：gs-fund-compare 的 get_data.py 里可离线验证的纯解析逻辑。

只测纯函数/解析函数（枚举映射、费率整合、规模/资产配置/风险解析、累计收益计算等），
绝不调用 query_* / compare_funds 等联网接口，避免真实请求。
"""
import unittest

import get_data as g


class TestMapEnumValue(unittest.TestCase):
    def test_known_mapping(self):
        self.assertEqual(g._map_enum_value("oftype", "1"), "股票型")

    def test_is_boolean_field(self):
        self.assertEqual(g._map_enum_value("isindex", "1"), "是")
        self.assertEqual(g._map_enum_value("isindex", "0"), "否")
        self.assertEqual(g._map_enum_value("estallow", "0"), "不支持")  # 走精确映射

    def test_strips_whitespace(self):
        self.assertEqual(g._map_enum_value("isindex", " 1 "), "是")

    def test_none_value_returns_empty(self):
        self.assertEqual(g._map_enum_value("oftype", None), "")

    def test_unmapped_value_returns_original(self):
        self.assertEqual(g._map_enum_value("oftype", "99"), "99")
        self.assertEqual(g._map_enum_value("nope", "1"), "1")


class TestFormatPercentage(unittest.TestCase):
    def test_normal(self):
        self.assertEqual(g._format_percentage("12.345"), "12.35%")

    def test_missing_returns_dashes(self):
        self.assertEqual(g._format_percentage(None), "--")
        self.assertEqual(g._format_percentage(""), "--")

    def test_garbage_returns_dashes(self):
        self.assertEqual(g._format_percentage("abc"), "--")


class TestMapRateEnumValue(unittest.TestCase):
    def test_feetype_mapping(self):
        self.assertEqual(g._map_rate_enum_value("feetype", "1"), "认购费率")
        self.assertEqual(g._map_rate_enum_value("feetype", "2"), "申购费率")
        self.assertEqual(g._map_rate_enum_value("feetype", "6"), "赎回费率")

    def test_other_field_uses_common_map(self):
        self.assertEqual(g._map_rate_enum_value("oftype", "1"), "股票型")

    def test_unmapped_and_empty(self):
        self.assertEqual(g._map_rate_enum_value("feetype", "9"), "9")
        self.assertEqual(g._map_rate_enum_value("feetype", None), "")


class TestMapManagerEnumValue(unittest.TestCase):
    def test_gender_and_sunrise(self):
        self.assertEqual(g._map_manager_enum_value("gender", "m"), "男")
        self.assertEqual(g._map_manager_enum_value("gender", "f"), "女")
        self.assertEqual(g._map_manager_enum_value("sunriseMgrFlag", "1"), "是")
        self.assertEqual(g._map_manager_enum_value("sunriseMgrFlag", "0"), "否")

    def test_unmapped_and_empty(self):
        self.assertEqual(g._map_manager_enum_value("mgrName", "张三"), "张三")
        self.assertEqual(g._map_manager_enum_value("mgrName", None), "")


class TestParseIntegratedRate(unittest.TestCase):
    def test_normal(self):
        rate_data = {"data": [
            {"fees": [{"managementfee": "1.5%", "storefee": "0.25%", "servicefee": "0.4%"}],
             "rates": [
                 {"feetype": "1", "feerange": "金额<100万", "freeratedesc": "1.2%", "ratefreedesc": "0.6%"},
                 {"feetype": "2", "feerange": "100万以上", "freeratedesc": "1.0%", "ratefreedesc": "1.0%"},
                 {"feetype": "6", "feerange": "<7天", "freeratedesc": "1.5%", "ratefreedesc": ""},
             ]}
        ]}
        out = g._parse_integrated_rate(rate_data)
        self.assertEqual(out["年管理费"], "1.5%")
        self.assertEqual(out["年托管费"], "0.25%")
        self.assertEqual(out["年销售服务费"], "0.4%")
        # 折后价不同才标"折后"，否则只写基准
        self.assertEqual(out["认购费率"], "金额<100万 1.2%(折后：0.6%)")
        self.assertEqual(out["申购费率"], "100万以上 1.0%")
        self.assertEqual(out["赎回费率"], "<7天 1.5%")

    def test_empty_input_returns_defaults(self):
        default = {"年管理费": "", "年托管费": "", "年销售服务费": "",
                   "认购费率": "", "申购费率": "", "赎回费率": ""}
        self.assertEqual(g._parse_integrated_rate({}), default)
        self.assertEqual(g._parse_integrated_rate({"data": []}), default)


class TestParseFundScale(unittest.TestCase):
    def test_normal(self):
        data = {"data1": [{"netvalue": 8.35, "enddate": "2025-12-31"}],
                "data2": [{"endshares": 14.62, "enddate": "2025-12-31"}],
                "data3": [{"institutionholdratio": 8.08, "individualholdratio": 91.92}]}
        out = g._parse_fund_scale(data)
        self.assertEqual(out["资产规模"], {"value": "8.35", "unit": "亿元", "date": "2025-12-31"})
        self.assertEqual(out["份额规模"], {"value": "14.62", "unit": "亿份", "date": "2025-12-31"})
        self.assertEqual(out["投资人结构"], {"机构占比": "8.08%", "个人占比": "91.92%"})

    def test_empty_returns_defaults(self):
        out = g._parse_fund_scale({})
        self.assertEqual(out["资产规模"], {"value": "", "unit": "", "date": ""})
        self.assertEqual(out["投资人结构"], {"机构占比": "", "个人占比": ""})


class TestParseAssetAllocation(unittest.TestCase):
    def test_normal(self):
        data = {"data1": [{"stockmvratioinnv": "60", "bondmvratioinnv": "30", "mfratioinnv": "5",
                           "fundmvratioinnv": "", "oaratioinnv": "5", "netvalue": "100",
                           "enddate": "2025-12-31"}]}
        out = g._parse_asset_allocation(data)
        self.assertEqual(out["股票占比"], "60")
        self.assertEqual(out["债券占比"], "30")
        self.assertEqual(out["报告期"], "2025-12-31")

    def test_empty_returns_defaults(self):
        out = g._parse_asset_allocation({})
        self.assertEqual(out["股票占比"], "")
        self.assertEqual(out["报告期"], "")


class TestParseTopHoldings(unittest.TestCase):
    def test_normal(self):
        data = {"data2": [{"holdingsecuabbr": "茅台", "ratioinnv": "8.5",
                           "firstindustry": "食品饮料", "stkcode": "600519",
                           "marketvalue": "1000", "rationinsv": "5"}]}
        out = g._parse_top_holdings(data)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["股票名称"], "茅台")
        self.assertEqual(out[0]["占净值比例"], "8.5")
        self.assertEqual(out[0]["申万行业"], "食品饮料")

    def test_empty(self):
        self.assertEqual(g._parse_top_holdings({}), [])


class TestParseRiskControl(unittest.TestCase):
    def test_normal_appends_percent(self):
        data = [{"period": "date_1y", "mdd": "10.5", "sharpe": "1.2", "std": "20.1",
                 "date": "2025-06-01"},
                {"period": "junk", "mdd": "1", "sharpe": "1"}]
        out = g._parse_risk_control(data)
        self.assertEqual(out["1y"], {"最大回撤": "10.5%", "夏普比率": "1.2",
                                     "波动率": "20.1%", "date": "2025-06-01"})
        # 不认识的周期被忽略，保持空默认
        self.assertEqual(out["3y"]["最大回撤"], "")
        self.assertEqual(out["5y"]["最大回撤"], "")

    def test_does_not_double_append_percent(self):
        data = [{"period": "date_1y", "mdd": "10.5%", "std": "20.1%", "sharpe": "1.2",
                 "date": ""}]
        out = g._parse_risk_control(data)
        self.assertEqual(out["1y"]["最大回撤"], "10.5%")

    def test_empty(self):
        out = g._parse_risk_control([])
        for k in ("1y", "3y", "5y"):
            self.assertEqual(out[k]["最大回撤"], "")


class TestCalculateCumulativeReturn(unittest.TestCase):
    def test_normal_and_fill_forward(self):
        data = [
            {"tradingdate": "20250101", "profit": "1.2", "profitIndex": "0.5"},
            {"tradingdate": "20250102", "profit": "-0.3", "profitIndex": ""},
            {"tradingdate": "20250103", "profit": "0.8", "profitIndex": "0.9"},
            {"tradingdate": "", "profit": "5", "profitIndex": "5"},
            {"tradingdate": "bad-date", "profit": "5", "profitIndex": "5"},
            {"tradingdate": "20250104", "profit": "", "profitIndex": "5"},
        ]
        dates, fund_returns, index_returns = g.calculate_cumulative_return(data)
        self.assertEqual([d.strftime("%Y%m%d") for d in dates],
                         ["20250101", "20250102", "20250103"])
        self.assertEqual(fund_returns, [1.2, -0.3, 0.8])
        # 缺失的沪深300收益用上一个有效值补齐
        self.assertEqual(index_returns, [0.5, 0.5, 0.9])

    def test_empty(self):
        self.assertEqual(g.calculate_cumulative_return([]), ([], [], []))


class TestFlattenValue(unittest.TestCase):
    def test_various(self):
        self.assertEqual(g._flatten_value(None), "")
        self.assertEqual(g._flatten_value({"a": 1}), '{"a": 1}')
        self.assertEqual(g._flatten_value("str"), "str")


class TestBuildComparisonTable(unittest.TestCase):
    def test_builds_rows_from_available_fields(self):
        funds = [{"ofcode": "000001", "secuabbr": "测试基金", "oftype": "1"}]
        rows = g._build_comparison_table(funds)
        labels = {r["字段"]: r for r in rows}
        self.assertIn("基金代码", labels)
        self.assertIn("基金简称", labels)
        self.assertEqual(labels["基金类型"]["测试基金"], "股票型")
        self.assertEqual(labels["基金代码"]["测试基金"], "000001")


if __name__ == "__main__":
    unittest.main()
