"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class BoothService(BaseModuleService):
    MODULE = "booth"
    ENTITY = "展位"
    OPERATION_TERM = "确认展位"
    LIST_FIELDS = ["展位编号", "面积尺寸", "开口方向", "所属区域", "登记编号", "负责人", "生效版本", "备注说明"]
    REQUIRED_FIELDS = ["展位编号", "面积尺寸", "开口方向"]
    STATUS_ORDER = ["草稿", "待确认", "已确认", "已撤回"]
    ACTION_RULES = {"确认展位": "已确认", "提交确认": "待确认", "撤回记录": "已撤回"}
    NEGATIVE_ACTIONS = []
