"""
cli.py - 命令行交互工具
提供友好的菜单界面，支持文档上传和智能问答
"""

import os
import sys
import asyncio
import httpx
from pathlib import Path
from typing import Optional
import json

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class Colors:
    """终端颜色代码"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_header():
    """打印标题"""
    print(f"\n{Colors.HEADER}{'=' * 60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}   📚 企业级智能文档分析平台 - 命令行助手{Colors.END}")
    print(f"{Colors.HEADER}{'=' * 60}{Colors.END}\n")


def print_menu():
    """打印主菜单"""
    print(f"{Colors.BOLD}请选择操作：{Colors.END}")
    print(f"  {Colors.GREEN}1{Colors.END}  📁 上传文档到知识库")
    print(f"  {Colors.GREEN}2{Colors.END}  💬 智能问答")
    print(f"  {Colors.GREEN}3{Colors.END}  📋 查看知识库列表")
    print(f"  {Colors.GREEN}4{Colors.END}  🗑️  删除知识库")
    print(f"  {Colors.GREEN}5{Colors.END}  🔄 批量上传 data/data_z 目录下的文档")
    print(f"  {Colors.GREEN}0{Colors.END}  🚪 退出")
    print()


def print_knowledge_bases(kb_list):
    """打印知识库列表"""
    if not kb_list:
        print(f"{Colors.YELLOW}📭 暂无知识库，请先创建{Colors.END}\n")
        return

    print(f"\n{Colors.BOLD}📚 知识库列表：{Colors.END}")
    print(f"{'ID':<6} {'名称':<20} {'文档数':<8} {'描述'}")
    print(f"{'-' * 50}")
    for kb in kb_list:
        print(
            f"{Colors.GREEN}{kb['id']:<6}{Colors.END} {kb['name']:<20} {kb.get('document_count', 0):<8} {kb.get('description', '')[:30]}")
    print()


async def create_knowledge_base(client, name: str, description: str = "") -> Optional[int]:
    """创建知识库"""
    try:
        response = await client.post(
            "http://localhost:8000/api/knowledge-bases",
            json={"name": name, "description": description}
        )
        if response.status_code == 200:
            data = response.json()
            kb_id = data['data']['id']
            print(f"{Colors.GREEN}✅ 知识库创建成功！ID: {kb_id}{Colors.END}")
            return kb_id
        else:
            print(f"{Colors.RED}❌ 创建失败: {response.text}{Colors.END}")
            return None
    except Exception as e:
        print(f"{Colors.RED}❌ 连接失败: {e}{Colors.END}")
        return None


async def upload_document(client, kb_id: int, file_path: str) -> bool:
    """上传文档"""
    try:
        file_name = Path(file_path).name
        file_ext = file_name.split('.')[-1].lower()

        if file_ext not in ['txt', 'pdf', 'docx']:
            print(f"{Colors.YELLOW}⚠️  跳过不支持的文件: {file_name} (仅支持 txt/pdf/docx){Colors.END}")
            return False

        with open(file_path, 'rb') as f:
            files = {"file": (file_name, f, f"application/{file_ext}")}
            data = {"knowledge_base_id": kb_id}

            response = await client.post(
                "http://localhost:8000/api/documents/upload",
                data=data,
                files=files
            )

        if response.status_code == 200:
            result = response.json()
            print(f"{Colors.GREEN}✅ 上传成功: {file_name} (分块数: {result['data']['chunk_count']}){Colors.END}")
            return True
        else:
            print(f"{Colors.RED}❌ 上传失败: {file_name} - {response.text}{Colors.END}")
            return False
    except Exception as e:
        print(f"{Colors.RED}❌ 上传失败 {file_path}: {e}{Colors.END}")
        return False


async def batch_upload_documents(client, kb_id: int, directory: str):
    """批量上传目录下的文档"""
    dir_path = Path(directory)
    if not dir_path.exists():
        print(f"{Colors.RED}❌ 目录不存在: {directory}{Colors.END}")
        return

    # 支持的格式
    extensions = ['*.txt', '*.pdf', '*.docx']
    files = []
    for ext in extensions:
        files.extend(dir_path.glob(ext))

    if not files:
        print(f"{Colors.YELLOW}⚠️  目录中没有找到支持的文档 (txt/pdf/docx){Colors.END}")
        return

    print(f"\n{Colors.BOLD}📁 找到 {len(files)} 个文档，开始上传...{Colors.END}\n")

    success_count = 0
    for file_path in files:
        print(f"  📄 {file_path.name} ... ", end="")
        if await upload_document(client, kb_id, str(file_path)):
            success_count += 1
        print()

    print(f"\n{Colors.GREEN}✅ 批量上传完成！成功: {success_count}/{len(files)}{Colors.END}")


async def list_knowledge_bases(client):
    """列出知识库"""
    try:
        response = await client.get("http://localhost:8000/api/knowledge-bases")
        if response.status_code == 200:
            data = response.json()
            print_knowledge_bases(data['data']['items'])
            return data['data']['items']
        else:
            print(f"{Colors.RED}❌ 获取失败: {response.text}{Colors.END}")
            return []
    except Exception as e:
        print(f"{Colors.RED}❌ 连接失败: {e}{Colors.END}")
        return []


async def delete_knowledge_base(client, kb_id: int):
    """删除知识库"""
    try:
        response = await client.delete(f"http://localhost:8000/api/knowledge-bases/{kb_id}")
        if response.status_code == 200:
            print(f"{Colors.GREEN}✅ 知识库 {kb_id} 已删除{Colors.END}")
            return True
        else:
            print(f"{Colors.RED}❌ 删除失败: {response.text}{Colors.END}")
            return False
    except Exception as e:
        print(f"{Colors.RED}❌ 连接失败: {e}{Colors.END}")
        return False


async def chat_loop(client, kb_id: int):
    """智能问答循环"""
    session_id = f"cli_session_{os.getpid()}"

    print(f"\n{Colors.BOLD}{Colors.CYAN}💬 进入问答模式 (输入 'quit' 退出，输入 'clear' 清空对话){Colors.END}\n")

    while True:
        try:
            question = input(f"{Colors.GREEN}你: {Colors.END}").strip()

            if not question:
                continue

            if question.lower() == 'quit':
                print(f"{Colors.YELLOW}👋 再见！{Colors.END}")
                break

            if question.lower() == 'clear':
                # 清空对话记忆（重新生成session_id）
                session_id = f"cli_session_{os.getpid()}_{int(asyncio.get_event_loop().time())}"
                print(f"{Colors.YELLOW}🧹 对话已清空{Colors.END}")
                continue

            # 发送请求
            print(f"{Colors.CYAN}🤖 思考中...{Colors.END}", end="\r")

            response = await client.post(
                "http://localhost:8000/api/chat",
                json={
                    "question": question,
                    "knowledge_base_id": kb_id,
                    "session_id": session_id
                },
                timeout=60
            )

            print(" " * 30, end="\r")  # 清除"思考中"字样

            if response.status_code == 200:
                data = response.json()
                answer = data['data']['answer']
                route = data['data']['route']

                # 显示路由类型
                route_icon = {
                    'chitchat': '💬',
                    'document': '📄',
                    'hybrid': '🔀',
                    'general': '🧠'
                }.get(route, '🤖')

                print(f"{Colors.BLUE}助手{Colors.END} [{route_icon} {route}]")
                print(f"{answer}\n")
            else:
                print(f"{Colors.RED}❌ 问答失败: {response.text}{Colors.END}")

        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}👋 再见！{Colors.END}")
            break
        except Exception as e:
            print(f"{Colors.RED}❌ 错误: {e}{Colors.END}")


async def select_knowledge_base(client, action_name: str) -> Optional[int]:
    """选择知识库"""
    kb_list = await list_knowledge_bases(client)

    if not kb_list:
        print(f"{Colors.YELLOW}📭 暂无知识库，请先创建{Colors.END}")

        create = input(f"{Colors.CYAN}是否创建新知识库？(y/n): {Colors.END}").strip().lower()
        if create == 'y':
            name = input(f"{Colors.CYAN}请输入知识库名称: {Colors.END}").strip()
            if name:
                return await create_knowledge_base(client, name)
        return None

    while True:
        try:
            kb_id = int(input(f"{Colors.CYAN}请输入知识库ID: {Colors.END}").strip())
            kb = next((k for k in kb_list if k['id'] == kb_id), None)
            if kb:
                print(f"{Colors.GREEN}✅ 已选择: {kb['name']}{Colors.END}")
                return kb_id
            else:
                print(f"{Colors.RED}❌ 知识库ID不存在，请重新输入{Colors.END}")
        except ValueError:
            print(f"{Colors.RED}❌ 请输入数字ID{Colors.END}")
        except KeyboardInterrupt:
            return None


async def main():
    """主函数"""
    print_header()

    # 检查服务是否运行
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.get("http://localhost:8000/health")
            if response.status_code != 200:
                print(f"{Colors.RED}❌ 服务未正常运行，请先启动服务: uvicorn app:app --reload{Colors.END}")
                return
    except Exception:
        print(f"{Colors.RED}❌ 无法连接到服务，请先启动服务: uvicorn app:app --reload{Colors.END}")
        print(f"   然后在另一个终端运行本程序{Colors.END}")
        return

    print(f"{Colors.GREEN}✅ 服务连接成功！{Colors.END}\n")

    async with httpx.AsyncClient(timeout=60) as client:
        while True:
            print_menu()

            try:
                choice = input(f"{Colors.BOLD}请输入选项 [0-5]: {Colors.END}").strip()

                if choice == '0':
                    print(f"{Colors.YELLOW}👋 再见！{Colors.END}")
                    break

                elif choice == '1':
                    # 上传文档
                    name = input(f"{Colors.CYAN}请输入知识库名称: {Colors.END}").strip()
                    if not name:
                        print(f"{Colors.RED}名称不能为空{Colors.END}")
                        continue

                    kb_id = await create_knowledge_base(client, name)
                    if kb_id:
                        file_path = input(f"{Colors.CYAN}请输入文档路径: {Colors.END}").strip()
                        if file_path and Path(file_path).exists():
                            await upload_document(client, kb_id, file_path)
                        else:
                            print(f"{Colors.RED}文件不存在{Colors.END}")

                elif choice == '2':
                    # 智能问答
                    kb_id = await select_knowledge_base(client, "问答")
                    if kb_id:
                        await chat_loop(client, kb_id)

                elif choice == '3':
                    # 查看知识库
                    await list_knowledge_bases(client)

                elif choice == '4':
                    # 删除知识库
                    kb_id = await select_knowledge_base(client, "删除")
                    if kb_id:
                        confirm = input(f"{Colors.RED}确认删除知识库 {kb_id}？(y/n): {Colors.END}").strip().lower()
                        if confirm == 'y':
                            await delete_knowledge_base(client, kb_id)

                elif choice == '5':
                    # 批量上传 data/data_z 目录
                    kb_id = await select_knowledge_base(client, "批量上传")
                    if kb_id:
                        await batch_upload_documents(client, kb_id, "data/data_z")

                else:
                    print(f"{Colors.RED}无效选项，请重新输入{Colors.END}")

                print()

            except KeyboardInterrupt:
                print(f"\n{Colors.YELLOW}👋 再见！{Colors.END}")
                break
            except Exception as e:
                print(f"{Colors.RED}错误: {e}{Colors.END}")


if __name__ == "__main__":
    asyncio.run(main())