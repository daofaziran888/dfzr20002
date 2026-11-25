"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class ChangeOrderService(BaseModuleService):
    MODULE = "change_order"
    ENTITY = "变更单"
    OPERATION_TERM = "签发变更"
    LIST_FIELDS = ["变更内容", "影响展位", "施工班组", "签收时限", "登记编号", "负责人", "生效版本", "备注说明"]
    REQUIRED_FIELDS = ["变更内容", "影响展位", "施工班组"]
    STATUS_ORDER = ["草稿", "待确认", "已确认", "已撤回"]
    ACTION_RULES = {"签发变更": "已确认", "提交确认": "待确认", "撤回记录": "已撤回"}
    NEGATIVE_ACTIONS = []
