"""
router_service.py - 智能路由服务

根据用户问题判断应该使用哪种问答模式
支持关键词匹配、优先级排序、配置热加载
"""

import yaml
import re
from typing import Dict, List, Tuple, Optional
from pathlib import Path
from utils.logger import get_logger

logger = get_logger(__name__)


class RouterService:
    """智能路由服务"""

    def __init__(self, config_path: str = "config/routing.yaml"):
        """
        初始化路由服务

        参数:
            config_path: 路由配置文件路径
        """
        self.config_path = config_path
        self.rules: Dict[str, dict] = {}
        self._load_config()
        logger.info(f"路由服务初始化完成，配置路径: {config_path}")

    def _load_config(self) -> dict:
        """
        加载路由配置

        返回:
            dict: 路由配置字典
        """
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                self.rules = config.get('routing', {})
                logger.info(f"路由配置加载成功，规则数: {len(self.rules)}")
                return self.rules
        except FileNotFoundError:
            logger.warning(f"配置文件不存在: {self.config_path}，使用默认配置")
            self._load_default_config()
            return self.rules
        except Exception as e:
            logger.error(f"加载路由配置失败: {e}")
            self._load_default_config()
            return self.rules

    def _load_default_config(self):
        """加载默认配置"""
        self.rules = {
            "chitchat": {
                "keywords": ["你好", "您好", "谢谢", "感谢", "再见", "拜拜", "嗨"],
                "priority": 1,
                "response": "你好！我是文档分析助手，有什么可以帮你的吗？"
            },
            "hybrid": {
                "keywords": ["你怎么看", "你的看法", "你的理解", "理解", "结合", "补充", "分析"],
                "priority": 2
            },
            "document": {
                "keywords": ["文档", "根据", "总结", "文章", "内容", "提到", "文中", "原文"],
                "priority": 3
            },
            "general": {
                "priority": 4
            }
        }
        logger.info("已加载默认路由配置")

    def _match_keywords(self, question: str, keywords: List[str]) -> bool:
        """
        关键词匹配（支持正则表达式）

        参数:
            question: 用户问题
            keywords: 关键词列表

        返回:
            bool: 是否匹配任意关键词
        """
        if not keywords:
            return False

        for keyword in keywords:
            # 检查是否包含正则表达式特殊字符
            if any(char in keyword for char in ['.*', '+', '?', '(', ')', '[', ']']):
                # 正则匹配
                if re.search(keyword, question):
                    return True
            else:
                # 普通字符串匹配
                if keyword in question:
                    return True
        return False

    def route(self, question: str) -> str:
        """
        路由判断，返回路由类型

        参数:
            question: 用户问题

        返回:
            str: 路由类型 (chitchat/document/general/hybrid)
        """
        if not question or not question.strip():
            logger.debug("问题为空，返回默认路由 general")
            return "general"

        # 按优先级排序（priority越小优先级越高）
        sorted_rules = sorted(
            self.rules.items(),
            key=lambda x: x[1].get('priority', 999)
        )

        for route_name, route_config in sorted_rules:
            keywords = route_config.get('keywords', [])
            if keywords and self._match_keywords(question, keywords):
                logger.debug(f"路由匹配: {route_name} (问题: {question[:50]}...)")
                return route_name

        logger.debug("无关键词匹配，返回默认路由 general")
        return "general"

    def get_explain(self, question: str) -> dict:
        """
        返回路由决策解释

        参数:
            question: 用户问题

        返回:
            dict: 包含路由类型、匹配关键词、优先级等信息的字典
        """
        if not question or not question.strip():
            return {
                "route": "general",
                "reason": "问题为空",
                "matched_keyword": None,
                "priority": self.rules.get("general", {}).get("priority", 4)
            }

        sorted_rules = sorted(
            self.rules.items(),
            key=lambda x: x[1].get('priority', 999)
        )

        for route_name, route_config in sorted_rules:
            keywords = route_config.get('keywords', [])
            if keywords:
                for keyword in keywords:
                    if self._match_keywords(question, [keyword]):
                        return {
                            "route": route_name,
                            "reason": f"匹配关键词: {keyword}",
                            "matched_keyword": keyword,
                            "priority": route_config.get('priority'),
                            "all_keywords": keywords
                        }

        return {
            "route": "general",
            "reason": "无关键词匹配，使用默认路由",
            "matched_keyword": None,
            "priority": self.rules.get("general", {}).get("priority", 4),
            "all_keywords": []
        }

    def get_response_for_chitchat(self) -> str:
        """
        获取闲聊回复

        返回:
            str: 闲聊场景的默认回复
        """
        chitchat_config = self.rules.get("chitchat", {})
        return chitchat_config.get(
            "response",
            "你好！我是文档分析助手，有什么可以帮你的吗？"
        )

    def reload_config(self):
        """
        热加载路由配置

        重新从配置文件加载路由规则，无需重启服务
        """
        logger.info("开始热加载路由配置...")
        self._load_config()
        logger.info("路由配置热加载完成")

    def get_all_routes(self) -> Dict[str, dict]:
        """
        获取所有路由规则

        返回:
            dict: 所有路由规则
        """
        return self.rules.copy()

    def add_custom_route(self, route_name: str, keywords: List[str], priority: int, **kwargs):
        """
        动态添加自定义路由

        参数:
            route_name: 路由名称
            keywords: 关键词列表
            priority: 优先级（数字越小优先级越高）
            **kwargs: 其他配置项
        """
        self.rules[route_name] = {
            "keywords": keywords,
            "priority": priority,
            **kwargs
        }
        logger.info(f"添加自定义路由: {route_name}, 优先级: {priority}")

    def remove_route(self, route_name: str) -> bool:
        """
        移除路由规则

        参数:
            route_name: 路由名称

        返回:
            bool: 是否移除成功
        """
        if route_name in self.rules:
            del self.rules[route_name]
            logger.info(f"移除路由: {route_name}")
            return True
        logger.warning(f"路由不存在: {route_name}")
        return False