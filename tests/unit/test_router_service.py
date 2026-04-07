"""
test_router_service.py - 路由服务单元测试
"""

import pytest
from core.services.router_service import RouterService


class TestRouterService:
    """路由服务测试类"""

    def setup_method(self):
        """测试前准备"""
        self.router = RouterService()

    def test_chitchat_routing(self):
        """测试闲聊路由"""
        test_cases = [
            ("你好", "chitchat"),
            ("谢谢你的帮助", "chitchat"),
            ("再见", "chitchat"),
        ]

        for question, expected in test_cases:
            result = self.router.route(question)
            assert result == expected, f"问题: {question}"

    def test_hybrid_routing(self):
        """测试混合路由"""
        test_cases = [
            ("你怎么看这个问题", "hybrid"),
            ("结合文档内容分析一下", "hybrid"),
            ("谈谈你的理解", "hybrid"),
        ]

        for question, expected in test_cases:
            result = self.router.route(question)
            assert result == expected, f"问题: {question}"

    def test_document_routing(self):
        """测试文档路由"""
        test_cases = [
            ("根据文档内容回答", "document"),
            ("总结一下这篇文章", "document"),
            ("文档里提到了什么", "document"),
        ]

        for question, expected in test_cases:
            result = self.router.route(question)
            assert result == expected, f"问题: {question}"

    def test_general_routing(self):
        """测试通用路由（默认）"""
        test_cases = [
            ("什么是人工智能", "general"),
            ("解释一下量子计算", "general"),
            ("", "general"),
        ]

        for question, expected in test_cases:
            result = self.router.route(question)
            assert result == expected, f"问题: {question}"

    def test_get_explain(self):
        """测试路由解释"""
        explain = self.router.get_explain("文档里说了什么")
        assert explain["route"] == "document"
        assert explain["matched_keyword"] is not None

    def test_reload_config(self):
        """测试配置热加载"""
        # 应该不抛出异常
        self.router.reload_config()

    def test_add_custom_route(self):
        """测试添加自定义路由"""
        self.router.add_custom_route(
            "coding",
            keywords=["Python", "代码"],
            priority=1
        )

        assert "coding" in self.router.get_all_routes()

        # 清理
        self.router.remove_route("coding")