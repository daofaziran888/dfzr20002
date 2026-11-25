<template>
  <section class="page">
    <header class="page-head">
      <div>
        <h2>运营概览</h2>
        <p class="page-desc">汇总各业务模块的关键指标，先看总量再看异常。</p>
      </div>
    </header>
    <div class="stat-row">
      <article v-for="card in cards" :key="card.label" class="stat-card">
        <span class="stat-label">{{ card.label }}</span>
        <strong class="stat-value">{{ card.value }}</strong>
      </article>
    </div>
    <table class="data-table">
      <thead>
        <tr><th>业务模块</th><th>今日新增</th><th>待处理</th><th>异常量</th></tr>
      </thead>
      <tbody>
        <tr v-for="row in moduleRows" :key="row.name">
          <td>{{ row.name }}</td>
          <td>{{ row.created }}</td>
          <td>{{ row.pending }}</td>
          <td>{{ row.abnormal }}</td>
        </tr>
      </tbody>
    </table>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import { fetchJson } from '@/api/client'

type Overview = {
  cards: { label: string; value: number }[]
  modules: { name: string; created: number; pending: number; abnormal: number }[]
}

const cards = ref<Overview['cards']>([])
const moduleRows = ref<Overview['modules']>([])

onMounted(async () => {
  try {
    const payload = await fetchJson<Overview>('/api/overview')
    cards.value = payload.cards
    moduleRows.value = payload.modules
  } catch {
    cards.value = [{"label": "业务模块", "value": 0}, {"label": "今日新增", "value": 0}]
    moduleRows.value = [{"name": "场馆规划", "created": 0, "pending": 0, "abnormal": 0}, {"name": "展位编排", "created": 0, "pending": 0, "abnormal": 0}, {"name": "参展商管理", "created": 0, "pending": 0, "abnormal": 0}, {"name": "方案设计", "created": 0, "pending": 0, "abnormal": 0}, {"name": "搭建物料", "created": 0, "pending": 0, "abnormal": 0}, {"name": "展品运输", "created": 0, "pending": 0, "abnormal": 0}, {"name": "搭建进度", "created": 0, "pending": 0, "abnormal": 0}, {"name": "用电配置", "created": 0, "pending": 0, "abnormal": 0}, {"name": "安全巡检", "created": 0, "pending": 0, "abnormal": 0}, {"name": "灯光编排", "created": 0, "pending": 0, "abnormal": 0}, {"name": "影音布置", "created": 0, "pending": 0, "abnormal": 0}, {"name": "家具配置", "created": 0, "pending": 0, "abnormal": 0}, {"name": "导视系统", "created": 0, "pending": 0, "abnormal": 0}, {"name": "验收清单", "created": 0, "pending": 0, "abnormal": 0}, {"name": "变更指令", "created": 0, "pending": 0, "abnormal": 0}, {"name": "布展排期", "created": 0, "pending": 0, "abnormal": 0}, {"name": "交场确认", "created": 0, "pending": 0, "abnormal": 0}, {"name": "突发事件", "created": 0, "pending": 0, "abnormal": 0}]
  }
})
</script>
