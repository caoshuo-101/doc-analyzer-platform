"""
chat.py - 聊天API路由

提供问答接口，支持普通和流式响应
"""

import time
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from typing import AsyncIterator

from api.schemas.common import ResponseModel
from api.schemas.chat import ChatRequest, ChatResponse, RouteExplainResponse
from api.dependencies import (
    get_router_service,
    get_search_service,
    get_conversation_service,
    get_model_gateway,
    get_session_id
)
from core.services.router_service import RouterService
from core.services.search_service import SearchService
from core.services.conversation_service import ConversationService
from infrastructure.llm.gateway import ModelGateway
from utils.prompt_loader import prompt_loader
from utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/chat", tags=["智能问答"])


@router.post("", response_model=ResponseModel)
async def chat(
    request: ChatRequest,
    router_service: RouterService = Depends(get_router_service),
    search_service: SearchService = Depends(get_search_service),
    conversation_service: ConversationService = Depends(get_conversation_service),
    model_gateway: ModelGateway = Depends(get_model_gateway)
):
    """
    普通问答接口

    - **question**: 用户问题
    - **knowledge_base_id**: 知识库ID
    - **session_id**: 会话ID（可选，不传则自动生成）
    """
    start_time = time.time()
    session_id = request.session_id or f"session_{int(start_time)}"

    # 1. 解析指代
    resolved_question = await conversation_service.resolve_reference(
        request.question,
        session_id
    )

    # 2. 保存用户消息
    await conversation_service.add_message(
        session_id=session_id,
        role="user",
        content=request.question,
        knowledge_base_id=request.knowledge_base_id
    )

    # 3. 路由判断
    route_type = router_service.route(resolved_question)
    route_explain = router_service.get_explain(resolved_question)
    logger.info(f"路由决策: {route_type}, 原因: {route_explain['reason']}")

    # 4. 根据路由类型生成回答
    if route_type == "chitchat":
        answer = router_service.get_response_for_chitchat()
        model_used = None

    elif route_type == "general":
        # 获取对话历史作为上下文
        context = await conversation_service.get_context_for_question(
            resolved_question,
            session_id,
            max_history=3
        )

        # 渲染提示词
        prompt = prompt_loader.render(
            "general_qa",
            question=resolved_question,
            context=context if context else "无历史对话"
        )

        # 调用模型
        answer = await model_gateway.generate(
            prompt=prompt,
            temperature=0.7,
            scene="general"
        )
        model_used = model_gateway.get_current_provider()

    else:  # document 或 hybrid
        # 检索相关文档
        context = await search_service.get_context(
            resolved_question,
            request.knowledge_base_id,
            top_k=3
        )

        # 获取对话历史
        history = await conversation_service.get_context_for_question(
            resolved_question,
            session_id,
            max_history=3
        )

        # 渲染提示词
        prompt_name = f"{route_type}_qa"
        prompt = prompt_loader.render(
            prompt_name,
            context=context,
            question=resolved_question,
            history=history if history else "无历史对话"
        )

        # 获取场景温度
        from config.settings import settings
        temperature = settings.get_temperature_for_scene(route_type)

        # 调用模型
        answer = await model_gateway.generate(
            prompt=prompt,
            temperature=temperature,
            scene=route_type
        )
        model_used = model_gateway.get_current_provider()

    # 5. 计算响应时间
    response_time_ms = int((time.time() - start_time) * 1000)

    # 6. 保存助手消息
    await conversation_service.add_message(
        session_id=session_id,
        role="assistant",
        content=answer,
        knowledge_base_id=request.knowledge_base_id,
        route_type=route_type,
        model_used=model_used,
        response_time_ms=response_time_ms
    )

    return ResponseModel(
        code=200,
        message="success",
        data=ChatResponse(
            answer=answer,
            route=route_type,
            session_id=session_id,
            model_used=model_used,
            response_time_ms=response_time_ms
        ).model_dump()
    )


@router.post("/stream")
async def stream_chat(
    request: ChatRequest,
    router_service: RouterService = Depends(get_router_service),
    search_service: SearchService = Depends(get_search_service),
    conversation_service: ConversationService = Depends(get_conversation_service),
    model_gateway: ModelGateway = Depends(get_model_gateway)
):
    """
    流式问答接口

    返回Server-Sent Events格式的流式响应
    """
    start_time = time.time()
    session_id = request.session_id or f"session_{int(start_time)}"

    # 解析指代
    resolved_question = await conversation_service.resolve_reference(
        request.question,
        session_id
    )

    # 保存用户消息
    await conversation_service.add_message(
        session_id=session_id,
        role="user",
        content=request.question,
        knowledge_base_id=request.knowledge_base_id
    )

    # 路由判断
    route_type = router_service.route(resolved_question)

    async def generate() -> AsyncIterator[str]:
        full_answer = ""

        if route_type == "chitchat":
            answer = router_service.get_response_for_chitchat()
            full_answer = answer
            yield f"data: {answer}\n\n"

        elif route_type == "general":
            # 获取对话历史
            context = await conversation_service.get_context_for_question(
                resolved_question,
                session_id,
                max_history=3
            )

            prompt = prompt_loader.render(
                "general_qa",
                question=resolved_question,
                context=context if context else "无历史对话"
            )

            async for chunk in model_gateway.stream_generate(prompt, temperature=0.7, scene="general"):
                full_answer += chunk
                yield f"data: {chunk}\n\n"

        else:
            # 检索相关文档
            context = await search_service.get_context(
                resolved_question,
                request.knowledge_base_id,
                top_k=3
            )

            history = await conversation_service.get_context_for_question(
                resolved_question,
                session_id,
                max_history=3
            )

            prompt_name = f"{route_type}_qa"
            prompt = prompt_loader.render(
                prompt_name,
                context=context,
                question=resolved_question,
                history=history if history else "无历史对话"
            )

            from config.settings import settings
            temperature = settings.get_temperature_for_scene(route_type)

            async for chunk in model_gateway.stream_generate(prompt, temperature=temperature, scene=route_type):
                full_answer += chunk
                yield f"data: {chunk}\n\n"

        # 保存助手消息
        response_time_ms = int((time.time() - start_time) * 1000)
        await conversation_service.add_message(
            session_id=session_id,
            role="assistant",
            content=full_answer,
            knowledge_base_id=request.knowledge_base_id,
            route_type=route_type,
            response_time_ms=response_time_ms
        )

        yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.delete("/conversations/{session_id}", response_model=ResponseModel)
async def clear_conversation(
    session_id: str,
    conversation_service: ConversationService = Depends(get_conversation_service)
):
    """
    清空会话记忆
    """
    await conversation_service.clear_memory(session_id)

    return ResponseModel(
        code=200,
        message=f"会话 {session_id} 已清空"
    )


@router.get("/route-explain", response_model=ResponseModel)
async def explain_route(
    question: str,
    router_service: RouterService = Depends(get_router_service)
):
    """
    解释路由决策

    返回路由判断的详细解释
    """
    explain = router_service.get_explain(question)

    return ResponseModel(
        code=200,
        message="success",
        data=RouteExplainResponse(
            route=explain["route"],
            reason=explain["reason"],
            matched_keyword=explain.get("matched_keyword"),
            priority=explain.get("priority")
        ).model_dump()
    )