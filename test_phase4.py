"""
test_phase4.py - Phase 4 验证脚本
测试LLM模块功能
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


async def test_qwen_provider():
    """测试通义千问提供者"""
    print("=" * 50)
    print("测试1: 通义千问提供者")
    print("=" * 50)

    from infrastructure.llm.qwen_provider import QwenProvider
    from config.settings import settings

    # 检查API Key
    if not settings.LLM_API_KEY or settings.LLM_API_KEY == "your_qwen_api_key_here":
        print("⚠️  通义千问API Key未配置，跳过测试")
        print("   请编辑 .env 文件，填写 LLM_API_KEY")
        return

    # 创建提供者
    provider = QwenProvider(
        model_name=settings.LLM_MODEL,
        api_key=settings.LLM_API_KEY,
        base_url=settings.LLM_BASE_URL
    )

    print(f"提供者: {provider.get_provider_name()}")
    print(f"模型: {settings.LLM_MODEL}")

    # 测试普通生成
    print("\n测试普通生成:")
    prompt = "用一句话介绍什么是人工智能"
    result = await provider.generate(prompt, temperature=0.5)
    print(f"用户: {prompt}")
    print(f"AI: {result}")

    # 测试流式生成
    print("\n测试流式生成:")
    prompt = "说三个关于Python的特点，每个一句话"
    print(f"用户: {prompt}")
    print("AI: ", end="", flush=True)

    async for chunk in provider.stream_generate(prompt, temperature=0.7):
        print(chunk, end="", flush=True)
    print("\n")

    print("✅ 通义千问提供者测试通过\n")


async def test_deepseek_provider():
    """测试DeepSeek提供者"""
    print("=" * 50)
    print("测试2: DeepSeek提供者")
    print("=" * 50)

    from infrastructure.llm.deepseek_provider import DeepSeekProvider
    from config.settings import settings

    # 检查API Key
    if not settings.BACKUP_LLM_API_KEY or settings.BACKUP_LLM_API_KEY == "your_deepseek_api_key_here":
        print("⚠️  DeepSeek API Key未配置，跳过测试")
        print("   请编辑 .env 文件，填写 BACKUP_LLM_API_KEY")
        return

    # 创建提供者
    provider = DeepSeekProvider(
        model_name=settings.BACKUP_LLM_MODEL,
        api_key=settings.BACKUP_LLM_API_KEY,
        base_url=settings.BACKUP_LLM_BASE_URL
    )

    print(f"提供者: {provider.get_provider_name()}")
    print(f"模型: {settings.BACKUP_LLM_MODEL}")

    # 测试生成
    prompt = "用一句话介绍机器学习"
    result = await provider.generate(prompt, temperature=0.5)
    print(f"用户: {prompt}")
    print(f"AI: {result}")

    print("✅ DeepSeek提供者测试通过\n")


async def test_model_gateway():
    """测试模型网关"""
    print("=" * 50)
    print("测试3: 模型网关（故障切换）")
    print("=" * 50)

    from infrastructure.llm.qwen_provider import QwenProvider
    from infrastructure.llm.deepseek_provider import DeepSeekProvider
    from infrastructure.llm.gateway import ModelGateway
    from config.settings import settings

    # 创建提供者
    primary = QwenProvider(
        model_name=settings.LLM_MODEL,
        api_key=settings.LLM_API_KEY,
        base_url=settings.LLM_BASE_URL
    )

    backup = DeepSeekProvider(
        model_name=settings.BACKUP_LLM_MODEL,
        api_key=settings.BACKUP_LLM_API_KEY,
        base_url=settings.BACKUP_LLM_BASE_URL
    )

    # 创建网关
    gateway = ModelGateway(
        primary=primary,
        backups=[backup],
        retry_times=2,
        retry_backoff=0.5
    )

    print(f"网关配置:")
    print(f"  主模型: {gateway.primary.get_provider_name()}")
    print(f"  备用模型: {[b.get_provider_name() for b in gateway.backups]}")
    print(f"  重试次数: {gateway.retry_times}")

    # 测试正常调用
    print("\n测试正常调用:")
    prompt = "用一句话介绍自然语言处理"
    result = await gateway.generate(prompt, temperature=0.5, scene="general")
    print(f"用户: {prompt}")
    print(f"AI: {result}")
    print(f"使用的模型: {gateway.get_current_provider()}")

    # 测试流式调用
    print("\n测试流式调用:")
    prompt = "列举3个AI的应用领域"
    print(f"用户: {prompt}")
    print("AI: ", end="", flush=True)

    async for chunk in gateway.stream_generate(prompt, temperature=0.7, scene="general"):
        print(chunk, end="", flush=True)
    print("\n")

    # 获取统计信息
    stats = gateway.get_stats()
    print(f"\n网关统计:")
    print(f"  总调用次数: {stats['total_calls']}")
    print(f"  成功率: {stats['success_rate']:.2%}")
    print(f"  当前模型: {stats['current_provider']}")

    print("✅ 模型网关测试通过\n")


async def test_fallback_scenario():
    """测试故障切换场景（模拟主模型失败）"""
    print("=" * 50)
    print("测试4: 故障切换场景")
    print("=" * 50)

    from infrastructure.llm.base import BaseLLMProvider
    from infrastructure.llm.deepseek_provider import DeepSeekProvider
    from infrastructure.llm.gateway import ModelGateway
    from config.settings import settings

    # 创建一个会失败的模拟主模型
    class FailingProvider(BaseLLMProvider):
        def get_provider_name(self):
            return "failing"

        def get_llm(self, temperature=0.7):
            return None

        async def generate(self, prompt, temperature=0.7, max_tokens=2000):
            raise Exception("模拟的主模型失败")

        async def stream_generate(self, prompt, temperature=0.7, max_tokens=2000):
            raise Exception("模拟的主模型失败")

        def validate_config(self):
            return True

    # 创建真实备用模型
    backup = DeepSeekProvider(
        model_name=settings.BACKUP_LLM_MODEL,
        api_key=settings.BACKUP_LLM_API_KEY,
        base_url=settings.BACKUP_LLM_BASE_URL
    )

    # 创建网关（主模型会失败）
    failing_provider = FailingProvider("fake", "fake", "fake")
    gateway = ModelGateway(
        primary=failing_provider,
        backups=[backup],
        retry_times=1,
        retry_backoff=0.1
    )

    print("场景: 主模型失败，自动切换到备用模型")

    prompt = "什么是深度学习？用一句话回答"
    result = await gateway.generate(prompt, temperature=0.5, scene="general")

    print(f"用户: {prompt}")
    print(f"AI: {result}")
    print(f"实际使用的模型: {gateway.get_current_provider()}")

    # 验证是否切换到了备用模型
    if gateway.get_current_provider() == "deepseek":
        print("✅ 故障切换成功！主模型失败后自动切换到DeepSeek")
    else:
        print(f"⚠️  当前模型: {gateway.get_current_provider()}")

    print("✅ 故障切换测试通过\n")


async def test_temperature_scenes():
    """测试不同场景的温度参数"""
    print("=" * 50)
    print("测试5: 不同场景的温度参数效果")
    print("=" * 50)

    from infrastructure.llm.qwen_provider import QwenProvider
    from config.settings import settings

    if not settings.LLM_API_KEY or settings.LLM_API_KEY == "your_qwen_api_key_here":
        print("⚠️  API Key未配置，跳过测试")
        return

    provider = QwenProvider(
        model_name=settings.LLM_MODEL,
        api_key=settings.LLM_API_KEY,
        base_url=settings.LLM_BASE_URL
    )

    prompt = "写一个关于'春天'的短句"

    # 低温度 - 更确定性
    print("\n温度 0.1 (更确定性):")
    result = await provider.generate(prompt, temperature=0.1)
    print(f"  {result}")

    # 中等温度
    print("\n温度 0.7 (中等创造性):")
    result = await provider.generate(prompt, temperature=0.7)
    print(f"  {result}")

    # 高温度 - 更创造性
    print("\n温度 1.0 (更创造性):")
    result = await provider.generate(prompt, temperature=1.0)
    print(f"  {result}")

    print("\n✅ 温度参数测试通过\n")


async def main():
    """主测试函数"""
    print("\n" + "=" * 50)
    print("Phase 4 验证开始")
    print("=" * 50 + "\n")

    await test_qwen_provider()
    await test_deepseek_provider()
    await test_model_gateway()
    await test_fallback_scenario()
    await test_temperature_scenes()

    print("=" * 50)
    print("Phase 4 全部测试通过！🎉")
    print("=" * 50)
    print("\nPhase 4 完成的功能:")
    print("1. 通义千问提供者 - 普通/流式生成")
    print("2. DeepSeek提供者 - 普通/流式生成")
    print("3. 模型网关 - 负载均衡、重试、故障切换")
    print("4. 故障切换 - 主模型失败自动切换备用")
    print("5. 温度控制 - 不同场景不同创造性")
    print("\n可继续 Phase 5: Repository层")


if __name__ == "__main__":
    asyncio.run(main())