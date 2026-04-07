"""
base.py - Repository基类

提供通用的CRUD操作，子类继承后自动获得基础能力
"""

from typing import Generic, TypeVar, Type, List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from core.models.base import BaseModel

# 泛型类型变量
ModelType = TypeVar("ModelType", bound=BaseModel)


class BaseRepository(Generic[ModelType]):
    """通用Repository基类"""

    def __init__(self, model: Type[ModelType], session: AsyncSession):
        """
        初始化Repository

        参数:
            model: SQLAlchemy模型类
            session: 异步数据库会话
        """
        self.model = model
        self.session = session

    async def create(self, **kwargs) -> ModelType:
        """
        创建新记录

        参数:
            **kwargs: 模型字段键值对

        返回:
            ModelType: 创建的模型实例
        """
        instance = self.model(**kwargs)
        self.session.add(instance)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def create_many(self, items: List[Dict[str, Any]]) -> List[ModelType]:
        """
        批量创建记录

        参数:
            items: 字典列表，每个字典包含模型字段键值对

        返回:
            List[ModelType]: 创建的模型实例列表
        """
        instances = [self.model(**item) for item in items]
        self.session.add_all(instances)
        await self.session.flush()
        for instance in instances:
            await self.session.refresh(instance)
        return instances

    async def get_by_id(self, id: int) -> Optional[ModelType]:
        """
        根据ID获取记录

        参数:
            id: 记录ID

        返回:
            Optional[ModelType]: 模型实例或None
        """
        result = await self.session.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()

    async def get_by_ids(self, ids: List[int]) -> List[ModelType]:
        """
        根据ID列表获取多条记录

        参数:
            ids: ID列表

        返回:
            List[ModelType]: 模型实例列表
        """
        if not ids:
            return []

        result = await self.session.execute(
            select(self.model).where(self.model.id.in_(ids))
        )
        return list(result.scalars().all())

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        order_by: Optional[str] = None,
        descending: bool = False
    ) -> List[ModelType]:
        """
        获取所有记录（分页）

        参数:
            skip: 跳过的记录数
            limit: 返回的最大记录数
            order_by: 排序字段
            descending: 是否降序

        返回:
            List[ModelType]: 模型实例列表
        """
        query = select(self.model)

        if order_by:
            order_column = getattr(self.model, order_by, self.model.id)
            if descending:
                query = query.order_by(order_column.desc())
            else:
                query = query.order_by(order_column)

        query = query.offset(skip).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update_by_id(self, id: int, **kwargs) -> Optional[ModelType]:
        """
        根据ID更新记录

        参数:
            id: 记录ID
            **kwargs: 要更新的字段键值对

        返回:
            Optional[ModelType]: 更新后的模型实例或None
        """
        # 先获取记录
        instance = await self.get_by_id(id)
        if not instance:
            return None

        # 更新字段
        for key, value in kwargs.items():
            if hasattr(instance, key):
                setattr(instance, key, value)

        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def update_many(self, ids: List[int], **kwargs) -> int:
        """
        批量更新记录

        参数:
            ids: ID列表
            **kwargs: 要更新的字段键值对

        返回:
            int: 更新的记录数
        """
        if not ids:
            return 0

        result = await self.session.execute(
            update(self.model)
            .where(self.model.id.in_(ids))
            .values(**kwargs)
        )
        await self.session.flush()
        return result.rowcount

    async def delete_by_id(self, id: int) -> bool:
        """
        根据ID删除记录

        参数:
            id: 记录ID

        返回:
            bool: 是否删除成功
        """
        instance = await self.get_by_id(id)
        if not instance:
            return False

        await self.session.delete(instance)
        await self.session.flush()
        return True

    async def delete_many(self, ids: List[int]) -> int:
        """
        批量删除记录

        参数:
            ids: ID列表

        返回:
            int: 删除的记录数
        """
        if not ids:
            return 0

        result = await self.session.execute(
            delete(self.model).where(self.model.id.in_(ids))
        )
        await self.session.flush()
        return result.rowcount

    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        统计记录数量

        参数:
            filters: 过滤条件（暂未实现复杂过滤）

        返回:
            int: 记录总数
        """
        query = select(func.count()).select_from(self.model)
        result = await self.session.execute(query)
        return result.scalar()

    async def exists(self, id: int) -> bool:
        """
        检查记录是否存在

        参数:
            id: 记录ID

        返回:
            bool: 是否存在
        """
        instance = await self.get_by_id(id)
        return instance is not None

    async def paginate(
        self,
        page: int = 1,
        per_page: int = 20,
        order_by: Optional[str] = None,
        descending: bool = False
    ) -> Dict[str, Any]:
        """
        分页获取记录

        参数:
            page: 页码（从1开始）
            per_page: 每页数量
            order_by: 排序字段
            descending: 是否降序

        返回:
            Dict: 包含items, total, page, per_page, pages的字典
        """
        # 获取总数
        total = await self.count()

        # 计算偏移量
        skip = (page - 1) * per_page

        # 获取数据
        items = await self.get_all(
            skip=skip,
            limit=per_page,
            order_by=order_by,
            descending=descending
        )

        # 计算总页数
        pages = (total + per_page - 1) // per_page if total > 0 else 1

        return {
            "items": items,
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": pages
        }