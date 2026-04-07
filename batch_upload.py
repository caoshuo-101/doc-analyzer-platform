"""
batch_upload.py - 批量上传 data/data_z 目录下的文档
运行后自动将目录中的所有 pdf、txt 文件上传到知识库
"""

import os
import sys
import asyncio
import httpx
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    CYAN = '\033[96m'
    END = '\033[0m'


async def upload_file(client, kb_id: int, file_path: Path) -> bool:
    """上传单个文件"""
    try:
        file_name = file_path.name
        file_ext = file_name.split('.')[-1].lower()

        # 检查文件类型
        if file_ext not in ['txt', 'pdf', 'docx']:
            print(f"  {Colors.YELLOW}⚠️ 跳过: {file_name} (不支持的类型){Colors.END}")
            return False

        # 读取文件并上传
        with open(file_path, 'rb') as f:
            files = {"file": (file_name, f, f"application/{file_ext}")}
            data = {"knowledge_base_id": kb_id}

            response = await client.post(
                "http://localhost:8000/api/documents/upload",
                data=data,
                files=files,
                timeout=120
            )

        if response.status_code == 200:
            result = response.json()
            print(f"  {Colors.GREEN}✅ 成功: {file_name} (分块: {result['data']['chunk_count']}){Colors.END}")
            return True
        else:
            print(f"  {Colors.RED}❌ 失败: {file_name} - {response.text[:100]}{Colors.END}")
            return False

    except Exception as e:
        print(f"  {Colors.RED}❌ 失败: {file_path.name} - {e}{Colors.END}")
        return False


async def create_knowledge_base(client, name: str) -> int:
    """创建知识库"""
    response = await client.post(
        "http://localhost:8000/api/knowledge-bases",
        json={"name": name, "description": "自动创建的知识库"}
    )

    if response.status_code == 200:
        kb_id = response.json()['data']['id']
        print(f"{Colors.GREEN}✅ 知识库创建成功: {name} (ID: {kb_id}){Colors.END}")
        return kb_id
    else:
        raise Exception(f"创建失败: {response.text}")


async def main():
    """主函数"""
    print(f"\n{Colors.CYAN}{'=' * 60}{Colors.END}")
    print(f"{Colors.CYAN}📚 批量文档上传工具{Colors.END}")
    print(f"{Colors.CYAN}{'=' * 60}{Colors.END}\n")

    # 检查服务
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get("http://localhost:8000/health")
            if resp.status_code != 200:
                print(f"{Colors.RED}❌ 服务未运行，请先启动: uvicorn app:app --reload{Colors.END}")
                return
    except:
        print(f"{Colors.RED}❌ 无法连接到服务，请先启动: uvicorn app:app --reload{Colors.END}")
        return

    print(f"{Colors.GREEN}✅ 服务连接成功{Colors.END}\n")

    # 检查目录
    doc_dir = Path("data/data_z")
    if not doc_dir.exists():
        print(f"{Colors.YELLOW}⚠️ 目录不存在，正在创建: {doc_dir}{Colors.END}")
        doc_dir.mkdir(parents=True, exist_ok=True)
        print(f"{Colors.YELLOW}📁 请将文档放入 {doc_dir} 目录后重新运行{Colors.END}")
        return

    # 查找文档
    files = []
    for ext in ['*.txt', '*.pdf', '*.docx']:
        files.extend(doc_dir.glob(ext))

    if not files:
        print(f"{Colors.YELLOW}⚠️ 目录中没有找到文档文件{Colors.END}")
        print(f"   支持的格式: .txt, .pdf, .docx")
        print(f"   请将文档放入: {doc_dir.absolute()}")
        return

    print(f"{Colors.CYAN}📁 找到 {len(files)} 个文档:{Colors.END}")
    for f in files:
        print(f"   - {f.name}")

    print()

    # 创建或选择知识库
    async with httpx.AsyncClient(timeout=120) as client:
        # 获取现有知识库
        resp = await client.get("http://localhost:8000/api/knowledge-bases")
        kb_list = resp.json().get('data', {}).get('items', []) if resp.status_code == 200 else []

        if kb_list:
            print(f"{Colors.CYAN}📚 已有知识库:{Colors.END}")
            for kb in kb_list:
                print(f"   {kb['id']}. {kb['name']} (文档数: {kb.get('document_count', 0)})")

            use_existing = input(f"\n{Colors.CYAN}使用已有知识库？(y/n，默认创建新知识库): {Colors.END}").strip().lower()

            if use_existing == 'y':
                kb_id = int(input(f"{Colors.CYAN}请输入知识库ID: {Colors.END}").strip())
                kb = next((k for k in kb_list if k['id'] == kb_id), None)
                if kb:
                    print(f"{Colors.GREEN}✅ 使用知识库: {kb['name']}{Colors.END}")
                else:
                    print(f"{Colors.RED}❌ 知识库不存在，将创建新知识库{Colors.END}")
                    kb_name = input(f"{Colors.CYAN}请输入新知识库名称: {Colors.END}").strip()
                    kb_name = kb_name or "批量上传知识库"
                    kb_id = await create_knowledge_base(client, kb_name)
            else:
                kb_name = input(f"{Colors.CYAN}请输入新知识库名称 (默认: 批量上传知识库): {Colors.END}").strip()
                kb_name = kb_name or "批量上传知识库"
                kb_id = await create_knowledge_base(client, kb_name)
        else:
            kb_name = input(f"{Colors.CYAN}请输入知识库名称 (默认: 批量上传知识库): {Colors.END}").strip()
            kb_name = kb_name or "批量上传知识库"
            kb_id = await create_knowledge_base(client, kb_name)

        print(f"\n{Colors.CYAN}开始上传文档...{Colors.END}\n")

        success = 0
        for file_path in files:
            if await upload_file(client, kb_id, file_path):
                success += 1

        print(f"\n{Colors.GREEN}{'=' * 60}{Colors.END}")
        print(f"{Colors.GREEN}📊 上传完成！成功: {success}/{len(files)}{Colors.END}")
        print(f"{Colors.GREEN}{'=' * 60}{Colors.END}")

        # 显示知识库统计
        resp = await client.get(f"http://localhost:8000/api/knowledge-bases/{kb_id}/stats")
        if resp.status_code == 200:
            stats = resp.json()['data']
            print(f"\n📚 知识库统计:")
            print(f"   总文档数: {stats['total']}")
            print(f"   总大小: {stats['total_size_mb']} MB")


if __name__ == "__main__":
    asyncio.run(main())