"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class ConstructionService(BaseModuleService):
    MODULE = "construction"
    ENTITY = "进度节点"
    OPERATION_TERM = "更新进度"
    LIST_FIELDS = ["节点名称", "计划日期", "完成日期", "前置节点", "登记编号", "负责人", "生效版本", "备注说明"]
    REQUIRED_FIELDS = ["节点名称", "计划日期", "完成日期"]
    STATUS_ORDER = ["草稿", "待确认", "已确认", "已撤回"]
    ACTION_RULES = {"更新进度": "已确认", "提交确认": "待确认", "撤回记录": "已撤回"}
    NEGATIVE_ACTIONS = []
