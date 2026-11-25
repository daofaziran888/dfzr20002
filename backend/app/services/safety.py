"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class SafetyService(BaseModuleService):
    MODULE = "safety"
    ENTITY = "巡检记录"
    OPERATION_TERM = "关闭隐患"
    LIST_FIELDS = ["检查点位", "隐患等级", "整改措施", "复查日期", "登记编号", "负责人", "生效版本", "备注说明"]
    REQUIRED_FIELDS = ["检查点位", "隐患等级", "整改措施"]
    STATUS_ORDER = ["草稿", "待确认", "已确认", "已撤回"]
    ACTION_RULES = {"关闭隐患": "已确认", "提交确认": "待确认", "撤回记录": "已撤回"}
    NEGATIVE_ACTIONS = []
