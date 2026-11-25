<template>
  <section class="page">
    <header class="page-head">
      <div>
        <h2>展位执行链</h2>
        <p class="page-desc">输入展位编号（如 BOOT-A01）查看从规划到交场的完整执行历史</p>
      </div>
    </header>

    <form class="filter-bar" @submit.prevent="queryHistory">
      <label class="filter-item">
        <span>展位编号</span>
        <input
          v-model="boothNo"
          placeholder="输入展位编号，如 BOOT-A01"
          data-testid="booth-input"
        />
      </label>
      <button class="btn primary" data-testid="query-history" type="submit">查询执行历史</button>
    </form>

    <p v-if="errorMessage" class="error-text">{{ errorMessage }}</p>

    <div v-if="history" class="history-view">
      <h3>展位：{{ history.booth_no }}</h3>

      <!-- 基本信息 -->
      <section class="info-card">
        <h4>基本信息</h4>
        <dl v-if="history.booth">
          <div v-for="(value, key) in basicInfo" :key="key">
            <dt>{{ key }}</dt>
            <dd>{{ value }}</dd>
          </div>
        </dl>
      </section>

      <!-- 设计方案 -->
      <section v-if="history.design" class="info-card">
        <h4>设计方案</h4>
        <p>设计风格：{{ history.design['设计风格'] }} | 用电负荷：{{ history.design['用电负荷'] }}kW</p>
      </section>

      <!-- 安全巡检 -->
      <section class="info-card">
        <h4>安全巡检状态</h4>
        <p :class="history.current_safety.ok ? 'text-success' : 'text-danger'">
          {{ history.current_safety.ok ? '全部通过' : '存在未通过项' }}
        </p>
        <p v-if="!history.current_safety.ok">
          未通过巡检 {{ history.current_safety.failed_inspections?.length || 0 }} 条
        </p>
      </section>

      <!-- 用电配额 -->
      <section class="info-card">
        <h4>用电配额</h4>
        <p v-if="history.current_electrical?.quota">
          设计负荷 {{ history.current_electrical.quota.design_load }}kW
          | 回路总功率 {{ history.current_electrical.quota.total_circuit_power }}kW
          <span v-if="history.current_electrical.quota.over_draw > 0" class="text-danger">
            （超载 {{ history.current_electrical.quota.over_draw }}kW）
          </span>
        </p>
      </section>

      <!-- 排期冲突 -->
      <section v-if="history.schedule_conflicts?.length" class="info-card">
        <h4>排期冲突</h4>
        <ul>
          <li v-for="(conflict, idx) in history.schedule_conflicts" :key="idx">
            {{ (conflict as Record<string, string>).conflict }}
          </li>
        </ul>
      </section>

      <!-- 执行事件时间线 -->
      <section class="info-card">
        <h4>执行事件（{{ history.event_count }} 条）</h4>
        <div v-if="history.events?.length" class="event-timeline">
          <article
            v-for="event in history.events"
            :key="event.id"
            class="event-item"
          >
            <span class="event-time">{{ formatTime(event.timestamp) }}</span>
            <span class="event-module">[{{ event.module }}]</span>
            <strong class="event-action">{{ event.action }}</strong>
            <span v-if="event.extra?.booth_no" class="event-detail">
              → {{ event.extra.booth_no }}
            </span>
            <span v-if="event.extra?.node_name" class="event-detail">
              {{ event.extra.node_name }}
            </span>
          </article>
        </div>
        <p v-else class="empty-state">暂无执行事件记录</p>
      </section>
    </div>
  </section>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { fetchBoothHistory, issueChangeOrder, signoffChecklist, confirmHandover } from '@/api/exhibition-client'
import type { ExhibitionHistory } from '@/data/exhibition-types'

const boothNo = ref('BOOT-A01')
const history = ref<ExhibitionHistory | null>(null)
const errorMessage = ref('')

const basicInfo = computed(() => {
  const booth = history.value?.booth
  if (!booth) return {}
  const info: Record<string, unknown> = {}
  const showFields = ['展位编号', '面积尺寸', '开口方向', '所属区域', '登记编号', '负责人', 'status']
  for (const f of showFields) {
    if (booth[f as string] !== undefined) info[f] = booth[f as string]
  }
  return info
})

function formatTime(ts: number): string {
  const d = new Date(ts * 1000)
  return d.toLocaleString('zh-CN', { hour12: false })
}

async function queryHistory() {
  errorMessage.value = ''
  try {
    history.value = null
    const result = await fetchBoothHistory(boothNo.value)
    history.value = result
  } catch (e) {
    errorMessage.value = e instanceof Error ? e.message : '查询失败'
  }
}
</script>

<style scoped>
.history-view { margin-top: 24px; }
.info-card {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
}
.info-card h4 { margin: 0 0 8px; color: #333; }
.info-card dl { margin: 0; }
.info-card dt { font-size: 12px; color: #999; }
.info-card dd { margin: 0 0 4px 0; font-size: 14px; }
.event-timeline { display: flex; flex-direction: column; gap: 8px; }
.event-item {
  display: flex; gap: 12px; align-items: center;
  padding: 8px; background: #fff; border-radius: 4px;
  font-size: 13px;
}
.event-time { color: #999; font-size: 12px; min-width: 140px; }
.event-module { color: #666; font-size: 12px; }
.event-action { color: #1890ff; }
.event-detail { color: #52c41a; }
.text-success { color: #52c41a; }
.text-danger { color: #f5222d; }
</style>