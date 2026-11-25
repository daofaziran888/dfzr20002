"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class LightingService(BaseModuleService):
    MODULE = "lighting"
    ENTITY = "灯光方案"
    OPERATION_TERM = "确认灯光"
    LIST_FIELDS = ["灯位坐标", "色温设定", "光束角度", "控制通道", "登记编号", "负责人", "生效版本", "备注说明"]
    REQUIRED_FIELDS = ["灯位坐标", "色温设定", "光束角度"]
    STATUS_ORDER = ["草稿", "待确认", "已确认", "已撤回"]
    ACTION_RULES = {"确认灯光": "已确认", "提交确认": "待确认", "撤回记录": "已撤回"}
    NEGATIVE_ACTIONS = []
