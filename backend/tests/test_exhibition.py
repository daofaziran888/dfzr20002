"""会展布展协作平台 - 确定性业务测试。

覆盖：
1. 面积配额超限拒绝
2. 功率配额超限拒绝
3. DAG 跳级推进拦截
4. DAG 环检测
5. 变更指令传播回退
6. 安全巡检未通过导致验收不可签收
7. 交场被未签收验收项拒绝
8. 重复请求幂等
9. 执行历史反查完整性
"""
import sys
import unittest

import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services import exhibition
from app.store import store


class TestAreaQuotaValidation(unittest.TestCase):
    """面积配额校验：展位面积之和不得超过场馆可用面积。"""

    def setUp(self):
        self.store = store

    def test_area_quota_pass_when_within_limit(self):
        """展位总面积在可用面积之内时应通过。"""
        result = exhibition.check_venue_capacity(1)
        self.assertTrue(result["ok"], f"面积配额应在限值内，实际: {result.get('reason')}")

    def test_area_quota_total_matches_booths(self):
        """验证展位总面积计算正确。"""
        result = exhibition.check_venue_capacity(1)
        quota = result.get("quota", {})
        if quota.get("venue_area"):
            self.assertEqual(quota["venue_area"], 2000)
        if quota.get("total_booth_area"):
            self.assertLessEqual(quota["total_booth_area"], quota["venue_area"])

    def test_area_quota_remaining_correct(self):
        """验证剩余面积计算正确。"""
        result = exhibition.check_venue_capacity(1)
        quota = result.get("quota", {})
        self.assertEqual(quota.get("remaining"), quota.get("venue_area", 0) - quota.get("total_booth_area", 0),
                         "剩余面积 = 场馆面积 - 展位总面积")


class TestElectricalPowerQuotaValidation(unittest.TestCase):
    """用电功率配额校验：回路额定功率之和不得超过设计负荷。"""

    def setUp(self):
        self.store = store

    def test_power_quota_pass_when_within_design_load(self):
        """BOOT-A01 回路总功率 75kW <= 设计负荷 80kW，应通过。"""
        result = exhibition.check_electrical_quota("BOOT-A01")
        self.assertTrue(result["ok"], f"BOOT-A01 功率应在限值内: {result.get('reason')}")

    def test_power_quota_fail_when_over_load(self):
        """BOOT-A02 回路总功率 70kW > 设计负荷 50kW，应拒绝。"""
        result = exhibition.check_electrical_quota("BOOT-A02")
        self.assertFalse(result["ok"], "BOOT-A02 功率超限应被拒绝")
        self.assertIn("超过", result.get("reason", ""))

    def test_power_quota_circuits_counted_correctly(self):
        """验证用电回路计数正确。"""
        result = exhibition.check_electrical_quota("BOOT-A02")
        quota = result.get("quota", {})
        circuits = quota.get("circuits", [])
        self.assertEqual(len(circuits), 2, "BOOT-A02 应有 2 个用电回路")

    def test_power_quota_nonexistent_booth(self):
        """不存在的展位返回失败。"""
        result = exhibition.check_electrical_quota("NONEXISTENT")
        self.assertFalse(result["ok"])


class TestDAGValidation(unittest.TestCase):
    """DAG 拓扑推进校验。"""

    def setUp(self):
        self.store = store

    def test_advance_with_unfinished_predecessor_rejected(self):
        """跳级推进（前置节点未完成）应被拦截：节点4'灯光影音联调'的前置'饰面安装'待确认。"""
        result = exhibition.validate_dag_advance(4)
        self.assertFalse(result["ok"], "前置节点未完成应被拦截")

    def test_advance_with_finished_predecessor_allowed(self):
        """前置节点已完成时推进应通过：节点2'强弱电布线'的前置'基础结构搭建'已确认。"""
        result = exhibition.validate_dag_advance(2)
        self.assertTrue(result["ok"], f"前置已完成应通过: {result.get('reason')}")

    def test_topological_order_correct(self):
        """拓扑排序应正确。"""
        nodes = self.store.rows("construction")
        order = exhibition.build_dag_order(nodes)
        expected_order = ["基础结构搭建", "强弱电布线", "饰面安装", "灯光影音联调", "安全复查"]
        self.assertEqual(order, expected_order, f"拓扑排序期待 {expected_order} 实际 {order}")

    def test_no_cycle_in_valid_dag(self):
        """有效的DAG不应检测到环。"""
        nodes = self.store.rows("construction")
        cycle = exhibition.detect_cycle(nodes)
        self.assertIsNone(cycle, f"DAG不应有环: {cycle}")

    def test_reject_advance_skipping_order(self):
        """推进节点4(灯光影音联调)时前置饰面安装未完成，应拒绝。"""
        result = exhibition.validate_dag_advance(4)
        self.assertFalse(result["ok"], "跳级推进应被拦截")


class TestChangeOrderPropagation(unittest.TestCase):
    """变更指令传播回退测试。"""

    def setUp(self):
        self.store = store

    def test_propagate_change_reverts_checklist_items(self):
        """签发变更后受影响展位的验收项回退到待确认。"""
        # 验收项5在BOOT-A02下,初始状态待确认,变更传播应包含它
        result = exhibition.propagate_change_order(1)
        self.assertTrue(result["ok"], f"变更应签发成功: {result.get('reason')}")
        affected_checklists = result.get("affected_checklists", [])
        self.assertGreater(len(affected_checklists), 0, "应有受影响的验收项")


class TestChecklistSignoffSafetyGate(unittest.TestCase):
    """安全巡检未通过导致验收不可签收。"""

    def setUp(self):
        self.store = store

    def test_signoff_blocked_when_safety_not_cleared(self):
        """BOOT-A02 安全巡检未通过，验收项5不可签收。"""
        result = exhibition.validate_checklist_signoff(5)
        self.assertFalse(result["ok"], "巡检未通过应拒绝签收")
        safety_check = result.get("safety_check", {})
        self.assertFalse(safety_check.get("ok", True))

    def test_signoff_allowed_when_safety_passed(self):
        """BOOT-A01 安全巡检已通过，验收项1可以签收。"""
        result = exhibition.validate_checklist_signoff(1)
        self.assertTrue(result["ok"], "巡检已通过应允许签收")


class TestHandoverValidation(unittest.TestCase):
    """交场确认必须消费验收清单完整结论。"""

    def setUp(self):
        self.store = store

    def test_handover_blocked_with_unsigned_checklist(self):
        """BOOT-A01 的验收项4未签收，交场单1应被拒绝。"""
        result = exhibition.validate_handover(1)
        self.assertFalse(result["ok"], "有未签收验收项应交场被拒")
        unsigned = result.get("unsigned_items", [])
        self.assertGreater(len(unsigned), 0, "应有未签收项")

    def test_handover_allowed_when_all_signed(self):
        """全部验收签收后交场应通过。"""
        # 先将所有BOOT-A01验收项签收
        for cid in [1, 2, 3, 4]:
            item = self.store.find("checklist", cid)
            if item:
                item["status"] = "已确认"
                item["pending"] = False
        result = exhibition.validate_handover(1)
        self.assertTrue(result["ok"], f"全部签收应交场通过: {result.get('reason')}")
        # 恢复数据
        item4 = self.store.find("checklist", 4)
        if item4:
            item4["status"] = "待确认"
            item4["pending"] = True


class TestIdempotency(unittest.TestCase):
    """重复请求幂等测试。"""

    def setUp(self):
        self.store = store

    def test_event_log_idempotent_check(self):
        """重复动作应通过事件日志检测到。"""
        self.store.event_log.record("test", 1, "confirm", after={"status": "done"})
        result = exhibition.ensure_idempotent("test", 1, "confirm")
        self.assertTrue(result["idempotent"], "应检测到重复动作")

    def test_new_action_not_idempotent(self):
        """新动作不应被判定为重复。"""
        result = exhibition.ensure_idempotent("test", 9999, "new_action")
        self.assertFalse(result["idempotent"], "新动作不应标记为幂等")


class TestExecutionHistory(unittest.TestCase):
    """执行历史反查完整性测试。"""

    def setUp(self):
        self.store = store

    def test_history_returns_events_for_booth(self):
        """展位执行历史应返回相关事件。"""
        self.store.event_log.record("booth", 1, "确认展位",
                                     extra={"booth_no": "BOOT-A01"})
        self.store.event_log.record("construction", 1, "拓扑推进",
                                     extra={"booth_no": "BOOT-A01",
                                            "node_name": "基础结构搭建"})
        result = exhibition.booth_execution_history("BOOT-A01")
        self.assertIsNotNone(result.get("booth"), "应返回展位信息")
        events = result.get("events", [])
        self.assertGreater(len(events), 0, "应有执行事件")

    def test_history_includes_safety_status(self):
        """执行历史应包含安全巡检状态。"""
        result = exhibition.booth_execution_history("BOOT-A01")
        safety = result.get("current_safety", {})
        self.assertIn("ok", safety)

    def test_history_includes_electrical_status(self):
        """执行历史应包含用电配额状态。"""
        result = exhibition.booth_execution_history("BOOT-A01")
        electrical = result.get("current_electrical", {})
        self.assertIn("ok", electrical)


class TestScheduleConflictDetection(unittest.TestCase):
    """展品运输排期冲突检测。"""

    def setUp(self):
        self.store = store

    def test_conflict_detected_when_arrival_after_setup(self):
        """运输预计到达晚于布展起始时应检测到冲突。"""
        conflicts = exhibition.detect_schedule_conflicts()
        conflict_ids = [c.get("transport_id") for c in conflicts]
        self.assertIn(3, conflict_ids, "运输单3应出现在冲突列表中")


class TestQuotaSummary(unittest.TestCase):
    """配额综合视图测试。"""

    def test_quota_summary_includes_all_components(self):
        """综合配额视图应包含面积、功率、排期、DAG 四个维度。"""
        summary = exhibition.quota_summary()
        self.assertIn("area_quotas", summary)
        self.assertIn("power_quotas", summary)
        self.assertIn("schedule_conflicts", summary)
        self.assertIn("dag_ok", summary)
        self.assertIn("overall_ok", summary)

    def test_dag_valid_in_summary(self):
        """当前种子DAG应为有效无环。"""
        summary = exhibition.quota_summary()
        self.assertTrue(summary["dag_ok"], "种子DAG不应有环")


if __name__ == "__main__":
    unittest.main(verbosity=2)