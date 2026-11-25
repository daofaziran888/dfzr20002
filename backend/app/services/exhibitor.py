"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class ExhibitorService(BaseModuleService):
    MODULE = "exhibitor"
    ENTITY = "参展商"
    OPERATION_TERM = "确认参展"
    LIST_FIELDS = ["企业名称", "展品类别", "联系人", "合同金额", "登记编号", "负责人", "生效版本", "备注说明"]
    REQUIRED_FIELDS = ["企业名称", "展品类别", "联系人"]
    STATUS_ORDER = ["草稿", "待确认", "已确认", "已撤回"]
    ACTION_RULES = {"确认参展": "已确认", "提交确认": "待确认", "撤回记录": "已撤回"}
    NEGATIVE_ACTIONS = []
