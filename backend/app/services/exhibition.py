"""会展布展协作引擎：跨模块面积/功率配额校验、DAG拓扑推进、变更传播回退、
交场门禁、冲突检测和执行历史重建。

所有领域规则集中在这里，每个模块 service 通过本引擎完成跨模块校验和联动。
"""
from __future__ import annotations

import copy
from collections import deque
from typing import Any

from app.store import store


# ---------- 面积配额 ----------

def check_venue_capacity(vendor_id: int) -> dict[str, Any]:
    """校验场馆内所有展位面积之和是否超过场馆可用面积。"""
    venue = store.find("venue", vendor_id)
    if venue is None:
        return {"ok": False, "reason": f"场馆 {vendor_id} 不存在", "quota": {}}

    try:
        venue_area = float(str(venue.get("可用面积", "0")).replace("平米", "").replace("㎡", "").strip())
    except (ValueError, AttributeError):
        return {"ok": False, "reason": "场馆可用面积字段无法解析", "quota": {}}

    all_booths = store.rows("booth")
    booth_areas: list[dict[str, Any]] = []
    total_booth_area = 0.0
    for booth in all_booths:
        booth_venue = str(booth.get("所属区域", ""))
        if booth_venue == str(venue.get("场馆名称", "")):
            try:
                area_text = str(booth.get("面积尺寸", "0")).replace("平米", "").replace("㎡", "").strip()
                area = float(area_text)
            except (ValueError, AttributeError):
                area = 0.0
            total_booth_area += area
            booth_areas.append({
                "booth_no": booth.get("展位编号", ""),
                "area": area,
                "status": booth.get("status", ""),
            })

    ok = total_booth_area <= venue_area
    return {
        "ok": ok,
        "reason": "" if ok else f"展位总面积 {total_booth_area}㎡ 超过场馆可用面积 {venue_area}㎡",
        "quota": {
            "venue_area": venue_area,
            "total_booth_area": total_booth_area,
            "remaining": venue_area - total_booth_area,
            "booths": booth_areas,
        },
    }


# ---------- 功率配额 ----------

def check_electrical_quota(booth_no: str) -> dict[str, Any]:
    """校验展位用电回路额定功率之和是否超过展位分配的设计负荷。"""
    booth = store.find_booth(booth_no)
    if booth is None:
        return {"ok": False, "reason": f"展位 {booth_no} 不存在", "quota": {}}

    designs = store.rows("design")
    design_load = 0.0
    for design in designs:
        d_booth = str(design.get("备注说明", ""))
        if d_booth == booth_no:
            try:
                design_load = float(str(design.get("用电负荷", "0")).replace("kW", "").strip())
            except (ValueError, AttributeError):
                design_load = 0.0
            break

    circuits = store.booth_electrical(booth_no)
    total_power = 0.0
    circuit_details: list[dict[str, Any]] = []
    for circuit in circuits:
        try:
            power = float(str(circuit.get("额定功率", "0")).replace("kW", "").replace("W", "").strip())
        except (ValueError, AttributeError):
            power = 0.0
        total_power += power
        circuit_details.append({
            "circuit_id": circuit.get("回路编号", ""),
            "power": power,
            "status": circuit.get("status", ""),
        })

    ok = True
    reason = ""
    if design_load > 0 and total_power > design_load:
        ok = False
        reason = f"用电回路总功率 {total_power}kW 超过展位 {booth_no} 的设计负荷 {design_load}kW"

    return {
        "ok": ok,
        "reason": reason,
        "quota": {
            "booth_no": booth_no,
            "design_load": design_load,
            "total_circuit_power": total_power,
            "over_draw": total_power - design_load if total_power > design_load else 0,
            "circuits": circuit_details,
        },
    }


# ---------- DAG 拓扑推进 ----------

def detect_cycle(nodes: list[dict[str, Any]]) -> list[str] | None:
    """检测前置节点依赖图中是否存在环，有环返回环上节点名称列表。"""
    name_to_id: dict[str, int] = {}
    for node in nodes:
        name = str(node.get("节点名称", ""))
        if name:
            name_to_id[name] = int(node.get("id", 0))

    graph: dict[str, list[str]] = {}
    for node in nodes:
        name = str(node.get("节点名称", ""))
        if not name:
            continue
        pred_text = str(node.get("前置节点", "")).strip()
        preds = [p.strip() for p in pred_text.split(",") if p.strip()]
        graph[name] = preds

    WHITE, GRAY, BLACK = 0, 1, 2
    color: dict[str, int] = {name: WHITE for name in graph}
    parent: dict[str, str | None] = {name: None for name in graph}

    def dfs(u: str) -> bool:
        color[u] = GRAY
        for v in graph.get(u, []):
            if v not in color:
                color[v] = WHITE
                parent[v] = u
                if dfs(v):
                    return True
            elif color.get(v) == GRAY:
                return True
        color[u] = BLACK
        return False

    for node_name in graph:
        if color.get(node_name) == WHITE:
            if dfs(node_name):
                # Find cycle by traversing back
                return [node_name]
    return None


def build_dag_order(nodes: list[dict[str, Any]]) -> list[str]:
    """返回拓扑排序后的节点名称列表。"""
    name_to_node: dict[str, dict[str, Any]] = {}
    for node in nodes:
        name = str(node.get("节点名称", ""))
        if name:
            name_to_node[name] = node

    pred_counts: dict[str, int] = {}
    successors: dict[str, list[str]] = {}
    for node in nodes:
        name = str(node.get("节点名称", ""))
        if not name:
            continue
        pred_text = str(node.get("前置节点", "")).strip()
        preds = [p.strip() for p in pred_text.split(",") if p.strip()]
        pred_counts[name] = len(preds)
        for pred in preds:
            successors.setdefault(pred, []).append(name)

    queue: deque[str] = deque()
    for name in name_to_node:
        if pred_counts.get(name, 0) == 0:
            queue.append(name)

    result: list[str] = []
    while queue:
        current = queue.popleft()
        result.append(current)
        for succ in successors.get(current, []):
            pred_counts[succ] -= 1
            if pred_counts[succ] == 0:
                queue.append(succ)

    return result


def validate_dag_advance(node_id: int) -> dict[str, Any]:
    """检查进度节点是否可以推进（所有前置节点必须已完成）。"""
    node = store.find("construction", node_id)
    if node is None:
        return {"ok": False, "reason": f"进度节点 {node_id} 不存在"}

    all_nodes = store.rows("construction")
    dag_order = build_dag_order(all_nodes)

    node_name = str(node.get("节点名称", ""))
    pred_text = str(node.get("前置节点", "")).strip()
    preds = [p.strip() for p in pred_text.split(",") if p.strip()]

    # 检测环
    cycle = detect_cycle(all_nodes)
    if cycle:
        return {"ok": False, "reason": f"前置依赖存在环：{cycle}", "cycle": cycle}

    # 检查每个前置节点是否已确认
    unfinished_preds: list[str] = []
    for pred_name in preds:
        pred_node = None
        for n in all_nodes:
            if str(n.get("节点名称", "")) == pred_name:
                pred_node = n
                break
        if pred_node and pred_node.get("status") != "已确认":
            unfinished_preds.append(pred_name)

    if unfinished_preds:
        return {
            "ok": False,
            "reason": f"前置节点未完成：{'、'.join(unfinished_preds)}，不能跳过前置节点",
            "unfinished_predecessors": unfinished_preds,
        }

    return {
        "ok": True,
        "reason": "前置条件已满足",
        "node": node_name,
        "predecessors": preds,
        "dag_order": dag_order,
    }


def topological_advance(node_id: int) -> dict[str, Any]:
    """推进进度节点（含 DAG 前置校验）。"""
    validation = validate_dag_advance(node_id)
    if not validation["ok"]:
        return validation

    node = store.find("construction", node_id)
    before_state = copy.deepcopy(node)
    node["status"] = "已确认"
    node["pending"] = False
    node["完成日期"] = validation.get("timestamp", "")

    store.event_log.record(
        module="construction",
        entry_id=node_id,
        action="拓扑推进",
        before=before_state,
        after=copy.deepcopy(node),
        extra={"node_name": node.get("节点名称", ""), "dag_order": validation.get("dag_order", [])},
    )
    return {"ok": True, "reason": f"节点 {node.get('节点名称', '')} 已推进", "node": node, "validation": validation}


# ---------- 安全巡检门禁 ----------

def check_safety_gate(booth_no: str) -> dict[str, Any]:
    """检查展位安全巡检是否全部通过（所有巡检记录状态为已确认）。"""
    inspections = store.booth_safety(booth_no)
    failed: list[dict[str, Any]] = []
    for insp in inspections:
        if insp.get("status") != "已确认":
            failed.append({
                "id": insp.get("id"),
                "point": insp.get("检查点位", ""),
                "level": insp.get("隐患等级", ""),
                "status": insp.get("status", ""),
            })

    return {
        "ok": len(failed) == 0,
        "reason": "" if len(failed) == 0 else f"展位 {booth_no} 有 {len(failed)} 条巡检未通过",
        "total_inspections": len(inspections),
        "failed_inspections": failed,
    }


# ---------- 验收签收门禁 ----------

def validate_checklist_signoff(checklist_id: int) -> dict[str, Any]:
    """验收签收前检查：安全巡检未通过时对应验收项不可签收。"""
    item = store.find("checklist", checklist_id)
    if item is None:
        return {"ok": False, "reason": f"验收项 {checklist_id} 不存在"}

    booth_no = str(item.get("负责班组", ""))
    safety_result = check_safety_gate(booth_no)
    if not safety_result["ok"]:
        return {
            "ok": False,
            "reason": f"展位 {booth_no} 安全巡检未通过，验收项「{item.get('验收条目', '')}」不可签收",
            "safety_check": safety_result,
        }

    return {"ok": True, "reason": "巡检已通过，可以签收", "item": item, "safety_check": safety_result}


# ---------- 交场门禁 ----------

def validate_handover(handover_id: int) -> dict[str, Any]:
    """交场确认必须消费验收清单的完整结论，未签收的验收项导致交场被拒。"""
    handover = store.find("handover", handover_id)
    if handover is None:
        return {"ok": False, "reason": f"交场单 {handover_id} 不存在"}

    booth_no = str(handover.get("遗留事项", ""))
    checklist_items = store.booth_checklist(booth_no)
    unsigned: list[dict[str, Any]] = []
    for item in checklist_items:
        if item.get("status") != "已确认":
            unsigned.append({
                "id": item.get("id"),
                "item": item.get("验收条目", ""),
                "status": item.get("status", ""),
            })

    if unsigned:
        return {
            "ok": False,
            "reason": f"展位 {booth_no} 有 {len(unsigned)} 条验收项未签收，交场被拒绝",
            "unsigned_items": unsigned,
            "checklist_total": len(checklist_items),
        }

    return {
        "ok": True,
        "reason": "验收清单全部签收，可以交场",
        "handover": handover,
        "checklist_total": len(checklist_items),
    }


def do_handover(handover_id: int) -> dict[str, Any]:
    """执行交场确认（含验收门禁校验）。"""
    validation = validate_handover(handover_id)
    if not validation["ok"]:
        return validation

    handover = store.find("handover", handover_id)
    before_state = copy.deepcopy(handover)
    handover["status"] = "已确认"
    handover["pending"] = False

    booth_no = str(handover.get("遗留事项", ""))
    store.event_log.record(
        module="handover",
        entry_id=handover_id,
        action="完成交场",
        before=before_state,
        after=copy.deepcopy(handover),
        extra={"booth_no": booth_no, "checklist_validated": True,
                "checklist_total": validation.get("checklist_total", 0)},
    )
    return {"ok": True, "reason": "交场完成", "handover": handover, "validation": validation}


# ---------- 变更传播与回退 ----------

def propagate_change_order(change_id: int) -> dict[str, Any]:
    """签发变更指令后，受影响展位的进度节点回到'待确认'并需要重新验收。"""
    change = store.find("change_order", change_id)
    if change is None:
        return {"ok": False, "reason": f"变更单 {change_id} 不存在"}

    booth_no_list = str(change.get("影响展位", "")).split(",")
    booth_no_list = [b.strip() for b in booth_no_list if b.strip()]
    affected_nodes: list[dict[str, Any]] = []
    affected_checklists: list[dict[str, Any]] = []

    for booth_no in booth_no_list:
        # 回退进度节点
        construction_nodes = store.rows("construction")
        for node in construction_nodes:
            node_booth = str(node.get("备注说明", ""))
            if booth_no in node_booth and node.get("status") == "已确认":
                node["status"] = "待确认"
                node["pending"] = True
                node["abnormal"] = True
                affected_nodes.append({"id": node.get("id"), "name": node.get("节点名称", "")})

        # 标记验收项需重新验收
        checklist_items = store.rows("checklist")
        for item in checklist_items:
            if str(item.get("负责班组", "")) == booth_no and item.get("status") == "已确认":
                item["status"] = "待确认"
                item["pending"] = True
                item["abnormal"] = True
                affected_checklists.append({"id": item.get("id"), "item": item.get("验收条目", "")})

    before_state = copy.deepcopy(change)
    change["status"] = "已确认"
    change["pending"] = False

    store.event_log.record(
        module="change_order",
        entry_id=change_id,
        action="签发变更-传播回退",
        before=before_state,
        after=copy.deepcopy(change),
        extra={
            "affected_booths": booth_no_list,
            "reverted_nodes": len(affected_nodes),
            "reverted_checklists": len(affected_checklists),
        },
    )
    store.rebuild_indices()

    return {
        "ok": True,
        "reason": f"变更已签发，{len(affected_nodes)} 个进度节点和 {len(affected_checklists)} 条验收项已回退",
        "affected_booths": booth_no_list,
        "affected_nodes": affected_nodes,
        "affected_checklists": affected_checklists,
    }


# ---------- 展品运输排期冲突检测 ----------

def detect_schedule_conflicts() -> list[dict[str, Any]]:
    """检测展品运输预计到达晚于布展起始时的排期冲突。"""
    transports = store.rows("transport")
    schedules = store.rows("schedule")
    conflicts: list[dict[str, Any]] = []

    for transport in transports:
        if transport.get("status") != "已确认":
            continue
        arrival = str(transport.get("预计到达", ""))
        for schedule in schedules:
            if schedule.get("status") != "已确认":
                continue
            setup_start = str(schedule.get("布展起始", ""))
            if arrival and setup_start and arrival > setup_start:
                conflicts.append({
                    "transport_id": transport.get("id"),
                    "exhibit": transport.get("展品名称", ""),
                    "arrival": arrival,
                    "schedule_id": schedule.get("id"),
                    "event": schedule.get("活动名称", ""),
                    "setup_start": setup_start,
                    "conflict": f"展品 {transport.get('展品名称', '')} 预计到达 {arrival} 晚于布展起始 {setup_start}",
                })

    return conflicts


# ---------- 执行历史重建 ----------

def booth_execution_history(booth_no: str) -> dict[str, Any]:
    """从事件日志中重建展位的完整执行历史。"""
    booth = store.find_booth(booth_no)
    events = store.event_log.for_booth(booth_no)

    # 也可能包含 booth 自身的事件
    for event in store.event_log.for_module("booth"):
        after = event.get("after") or {}
        if after.get("展位编号") == booth_no:
            if event not in events:
                events.append(event)

    events.sort(key=lambda e: e["timestamp"])

    # 汇总当前状态
    design = None
    for d in store.rows("design"):
        if str(d.get("备注说明", "")) == booth_no:
            design = d
            break

    return {
        "booth_no": booth_no,
        "booth": booth,
        "design": design,
        "events": events,
        "event_count": len(events),
        "current_safety": check_safety_gate(booth_no),
        "current_electrical": check_electrical_quota(booth_no),
        "schedule_conflicts": [c for c in detect_schedule_conflicts()
                                if booth_no in str(c)],
    }


# ---------- 幂等请求识别 ----------

def ensure_idempotent(module: str, entry_id: int, action: str) -> dict[str, Any]:
    """检查请求是否已经处理过（基于事件日志），返回已处理结果或 None。"""
    for event in reversed(store.event_log.for_module(module, entry_id)):
        if event["action"] == action:
            after = event.get("after")
            if after:
                return {"idempotent": True, "cached_result": after, "event_id": event["id"]}
    return {"idempotent": False}


# ---------- 配额综合视图 ----------

def quota_summary() -> dict[str, Any]:
    """全场面积配额与功率配额的综合结论。"""
    venues = store.rows("venue")
    booths = store.rows("booth")
    quota_results: list[dict[str, Any]] = []

    for venue in venues:
        if venue.get("status") != "已确认":
            continue
        v_result = check_venue_capacity(int(venue.get("id", 0)))
        quota_results.append({
            "venue": venue.get("场馆名称", ""),
            "venue_id": venue.get("id"),
            **v_result,
        })

    booth_power_results: list[dict[str, Any]] = []
    for booth in booths:
        if booth.get("status") != "已确认":
            continue
        booth_no = str(booth.get("展位编号", ""))
        if booth_no:
            p_result = check_electrical_quota(booth_no)
            if p_result.get("quota"):
                booth_power_results.append(p_result)

    schedule_conflicts = detect_schedule_conflicts()
    dag_cycle = detect_cycle(store.rows("construction"))

    return {
        "area_quotas": quota_results,
        "power_quotas": booth_power_results,
        "schedule_conflicts": schedule_conflicts,
        "schedule_conflict_count": len(schedule_conflicts),
        "dag_cycle": dag_cycle,
        "dag_ok": dag_cycle is None,
        "overall_ok": all(q.get("ok", True) for q in quota_results)
                       and all(p.get("ok", True) for p in booth_power_results)
                       and len(schedule_conflicts) == 0
                       and dag_cycle is None,
    }