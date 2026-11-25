"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class FurnitureService(BaseModuleService):
    MODULE = "furniture"
    ENTITY = "家具方案"
    OPERATION_TERM = "确认配置"
    LIST_FIELDS = ["家具类型", "摆放位置", "数量需求", "风格色调", "登记编号", "负责人", "生效版本", "备注说明"]
    REQUIRED_FIELDS = ["家具类型", "摆放位置", "数量需求"]
    STATUS_ORDER = ["草稿", "待确认", "已确认", "已撤回"]
    ACTION_RULES = {"确认配置": "已确认", "提交确认": "待确认", "撤回记录": "已撤回"}
    NEGATIVE_ACTIONS = []
