"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class ElectricalService(BaseModuleService):
    MODULE = "electrical"
    ENTITY = "用电回路"
    OPERATION_TERM = "核验用电"
    LIST_FIELDS = ["回路编号", "额定功率", "所属展位", "断路器型号", "登记编号", "负责人", "生效版本", "备注说明"]
    REQUIRED_FIELDS = ["回路编号", "额定功率", "所属展位"]
    STATUS_ORDER = ["草稿", "待确认", "已确认", "已撤回"]
    ACTION_RULES = {"核验用电": "已确认", "提交确认": "待确认", "撤回记录": "已撤回"}
    NEGATIVE_ACTIONS = []
