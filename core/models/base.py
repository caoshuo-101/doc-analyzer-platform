"""
base.py - 模型基类

定义所有数据模型的公共字段和方法
"""

from sqlalchemy import Column, Integer, DateTime
from sqlalchemy.sql import func
from infrastructure.database.connection import Base


class BaseModel(Base):
    """所有模型的基类"""

    __abstract__ = True  # 不创建表

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def to_dict(self) -> dict:
        """
        将模型实例转换为字典

        返回:
            dict: 包含所有字段的字典
        """
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }