"""
test_api_knowledge_bases.py - 知识库API集成测试
"""

import pytest
from httpx import AsyncClient


class TestKnowledgeBasesAPI:
    """知识库API测试类"""

    @pytest.mark.asyncio
    async def test_create_knowledge_base(self, client: AsyncClient):
        """测试创建知识库"""
        response = await client.post(
            "/api/knowledge-bases",
            json={
                "name": "测试知识库",
                "description": "集成测试用"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["name"] == "测试知识库"

        # 保存ID供后续测试
        return data["data"]["id"]

    @pytest.mark.asyncio
    async def test_list_knowledge_bases(self, client: AsyncClient):
        """测试获取知识库列表"""
        response = await client.get("/api/knowledge-bases")

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "items" in data["data"]

    @pytest.mark.asyncio
    async def test_get_knowledge_base(self, client: AsyncClient):
        """测试获取知识库详情"""
        # 先创建
        create_response = await client.post(
            "/api/knowledge-bases",
            json={"name": "详情测试库"}
        )
        kb_id = create_response.json()["data"]["id"]

        # 再获取
        response = await client.get(f"/api/knowledge-bases/{kb_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["id"] == kb_id

    @pytest.mark.asyncio
    async def test_update_knowledge_base(self, client: AsyncClient):
        """测试更新知识库"""
        # 先创建
        create_response = await client.post(
            "/api/knowledge-bases",
            json={"name": "更新测试库"}
        )
        kb_id = create_response.json()["data"]["id"]

        # 再更新
        response = await client.put(
            f"/api/knowledge-bases/{kb_id}",
            json={"description": "已更新"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["description"] == "已更新"

    @pytest.mark.asyncio
    async def test_delete_knowledge_base(self, client: AsyncClient):
        """测试删除知识库"""
        # 先创建
        create_response = await client.post(
            "/api/knowledge-bases",
            json={"name": "删除测试库"}
        )
        kb_id = create_response.json()["data"]["id"]

        # 再删除
        response = await client.delete(f"/api/knowledge-bases/{kb_id}")

        assert response.status_code == 200

        # 验证已删除
        get_response = await client.get(f"/api/knowledge-bases/{kb_id}")
        assert get_response.status_code == 404