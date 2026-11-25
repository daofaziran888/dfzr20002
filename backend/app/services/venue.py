"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class VenueService(BaseModuleService):
    MODULE = "venue"
    ENTITY = "场馆"
    OPERATION_TERM = "确认场馆"
    LIST_FIELDS = ["场馆名称", "可用面积", "层高限制", "地面承重", "登记编号", "负责人", "生效版本", "备注说明"]
    REQUIRED_FIELDS = ["场馆名称", "可用面积", "层高限制"]
    STATUS_ORDER = ["草稿", "待确认", "已确认", "已撤回"]
    ACTION_RULES = {"确认场馆": "已确认", "提交确认": "待确认", "撤回记录": "已撤回"}
    NEGATIVE_ACTIONS = []
