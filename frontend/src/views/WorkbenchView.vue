<template>
  <section class="page" :data-module="meta.key">
    <header class="page-head">
      <div>
        <h2>{{ meta.name }}</h2>
        <p class="page-desc">{{ meta.desc }}</p>
      </div>
      <div class="page-actions">
        <button class="btn primary" data-testid="open-create" type="button" @click="openCreate">
          登记{{ meta.entity }}
        </button>
        <button class="btn" data-testid="export" type="button" @click="exportRows">
          导出{{ meta.name }}清单
        </button>
      </div>
    </header>

    <div class="stat-row">
      <article v-for="item in stats" :key="item.label" class="stat-card">
        <span class="stat-label">{{ item.label }}</span>
        <strong class="stat-value">{{ item.value }}</strong>
      </article>
    </div>

    <p class="status-legend">
      <span v-for="item in statusSummary" :key="item.status" class="legend-item">
        {{ item.status }}：{{ item.count }}
      </span>
    </p>

    <form class="filter-bar" @submit.prevent="reload">
      <label v-for="field in filterFields" :key="field" class="filter-item">
        <span>{{ field }}</span>
        <input v-model="filters[field]" :data-testid="`filter-${field}`" :placeholder="`按${field}检索`" />
      </label>
      <button class="btn" data-testid="query" type="submit">查询</button>
      <button class="btn ghost" data-testid="reset" type="button" @click="resetFilters">重置条件</button>
    </form>

    <table class="data-table">
      <thead>
        <tr>
          <th v-for="column in meta.fields" :key="column">{{ column }}</th>
          <th>当前状态</th>
          <th>可执行动作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="row in rows" :key="String(row.id)" :data-testid="`row-${row.id}`" :data-status="String(row.status)">
          <td v-for="column in meta.fields" :key="column">{{ row[column] ?? '—' }}</td>
          <td>{{ row.status }}</td>
          <td class="row-actions">
            <button
              v-for="action in meta.actions"
              :key="action"
              class="link"
              type="button"
              :data-testid="`action-${row.id}-${action}`"
              @click="runAction(action, row)"
            >
              {{ action }}
            </button>
          </td>
        </tr>
        <tr v-if="!rows.length">
          <td :colspan="meta.fields.length + 2" class="empty-state">
            暂无{{ meta.name }}数据，可先登记{{ meta.entity }}
          </td>
        </tr>
      </tbody>
    </table>

    <div v-if="showCreate" class="modal-backdrop" data-testid="create-modal">
      <form class="modal" @submit.prevent="submitCreate">
        <h3>登记{{ meta.entity }}</h3>
        <label v-for="field in meta.fields" :key="field" class="create-field">
          <span>{{ field }}</span>
          <input v-model="createValues[field]" :data-testid="`create-${field}`" required />
        </label>
        <div class="page-actions">
          <button class="btn" type="button" @click="showCreate = false">取消</button>
          <button class="btn primary" data-testid="submit-create" type="submit" :disabled="creating">
            {{ creating ? '提交中…' : '确认登记' }}
          </button>
        </div>
      </form>
    </div>

    <footer class="page-foot">
      <span>共 {{ total }} 条{{ meta.name }}记录</span>
      <span v-if="errorMessage" class="error-text">{{ errorMessage }}</span>
    </footer>

    <section v-if="crossSnapshot && crossSnapshot.ok" class="cross-module-panel">
      <h3>跨模块关联视图：展位 {{ crossSnapshot.booth_no }}</h3>
      <div class="cross-grid">
        <div class="cross-card" v-if="crossSnapshot.venue">
          <span class="cross-label">所属场馆</span>
          <strong>{{ crossSnapshot.venue['场馆名称'] }}</strong>
          <small>{{ crossSnapshot.venue['可用面积'] }}㎡ / {{ crossSnapshot.venue['层高限制'] }}</small>
        </div>
        <div class="cross-card" v-if="crossSnapshot.exhibitors?.length">
          <span class="cross-label">参展商</span>
          <strong>{{ crossSnapshot.exhibitors.length }} 家</strong>
          <small>{{ crossSnapshot.exhibitors.map((e: any) => e['企业名称']).join('、') }}</small>
        </div>
        <div class="cross-card" v-if="crossSnapshot.designs?.length">
          <span class="cross-label">设计方案</span>
          <strong>{{ crossSnapshot.designs.length }} 套</strong>
          <small>风格: {{ crossSnapshot.designs.map((d: any) => d['设计风格']).join('、') }}</small>
        </div>
        <div class="cross-card" v-if="crossSnapshot.materials?.length">
          <span class="cross-label">搭建物料</span>
          <strong>{{ crossSnapshot.materials.length }} 种</strong>
          <small>{{ crossSnapshot.materials.map((m: any) => m['物料名称']).join('、') }}</small>
        </div>
        <div class="cross-card" v-if="crossSnapshot.electricals?.length">
          <span class="cross-label">用电回路</span>
          <strong>{{ crossSnapshot.electricals.length }} 路</strong>
          <small>总功率: {{ computeTotalPower(crossSnapshot.electricals) }}kW</small>
        </div>
        <div class="cross-card" v-if="crossSnapshot.constructions?.length">
          <span class="cross-label">进度节点</span>
          <strong>{{ crossSnapshot.constructions.length }} 个</strong>
          <small>已确认: {{ crossSnapshot.constructions.filter((c: any) => c.status === '已确认').length }}</small>
        </div>
        <div class="cross-card" v-if="crossSnapshot.checklists?.length">
          <span class="cross-label">验收清单</span>
          <strong>{{ crossSnapshot.checklists.length }} 条</strong>
          <small>已签收: {{ crossSnapshot.checklists.filter((c: any) => c.status === '已确认').length }}</small>
        </div>
        <div class="cross-card" v-if="crossSnapshot.safeties?.length">
          <span class="cross-label">安全巡检</span>
          <strong>{{ crossSnapshot.safeties.length }} 条</strong>
          <small>已通过: {{ crossSnapshot.safeties.filter((s: any) => s.status === '已确认').length }}</small>
        </div>
        <div class="cross-card" v-if="crossSnapshot.lightings?.length">
          <span class="cross-label">灯光方案</span>
          <strong>{{ crossSnapshot.lightings.length }} 套</strong>
        </div>
        <div class="cross-card" v-if="crossSnapshot.audio_visuals?.length">
          <span class="cross-label">影音设备</span>
          <strong>{{ crossSnapshot.audio_visuals.length }} 台</strong>
        </div>
        <div class="cross-card" v-if="crossSnapshot.furnitures?.length">
          <span class="cross-label">家具配置</span>
          <strong>{{ crossSnapshot.furnitures.length }} 套</strong>
        </div>
        <div class="cross-card" v-if="crossSnapshot.change_orders?.length">
          <span class="cross-label">变更指令</span>
          <strong>{{ crossSnapshot.change_orders.length }} 条</strong>
          <small>{{ crossSnapshot.change_orders.map((co: any) => co['变更内容']).join('；') }}</small>
        </div>
        <div class="cross-card" v-if="crossSnapshot.handovers?.length">
          <span class="cross-label">交场确认</span>
          <strong>{{ crossSnapshot.handovers.length }} 单</strong>
        </div>
        <div class="cross-card" v-if="crossSnapshot.incidents?.length">
          <span class="cross-label">突发事件</span>
          <strong>{{ crossSnapshot.incidents.length }} 起</strong>
        </div>
      </div>
    </section>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'

import {
  createEntry,
  downloadEntries,
  listEntries,
  moduleMeta,
  runAction as applyAction,
} from '@/api/backend-service'
import { fetchJson } from '@/api/client'
import type { EntryRow } from '@/data/types'

const props = defineProps<{ moduleKey: string }>()
const meta = moduleMeta(props.moduleKey)
const rows = ref<EntryRow[]>([])
const total = ref(0)
const errorMessage = ref('')
const filters = ref<Record<string, string>>({})
const filterFields = meta.fields.slice(0, 3)
const showCreate = ref(false)
const creating = ref(false)
const createValues = ref<Record<string, string>>({})
const stats = computed(() => [
  { label: meta.metrics[0], value: total.value },
  { label: meta.metrics[1], value: rows.value.filter((row) => row.status === meta.statuses[1]).length },
  {
    label: meta.metrics[2],
    value: rows.value.filter((row) => row.status === meta.statuses[meta.statuses.length - 1]).length,
  },
])
const statusSummary = computed(() =>
  meta.statuses.map((status) => ({
    status,
    count: rows.value.filter((row) => String(row.status) === status).length,
  })),
)

function resetFilters() {
  filters.value = {}
  void reload()
}

async function exportRows() {
  errorMessage.value = ''
  try {
    await downloadEntries(meta.key, filters.value)
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '导出失败'
  }
}

function openCreate() {
  createValues.value = Object.fromEntries(meta.fields.map((field) => [field, '']))
  errorMessage.value = ''
  showCreate.value = true
}

async function submitCreate() {
  creating.value = true
  errorMessage.value = ''
  try {
    const result = await createEntry(meta.key, createValues.value)
    if (!result.ok) throw new Error(result.message)
    showCreate.value = false
    await reload()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '登记失败'
  } finally {
    creating.value = false
  }
}

async function runAction(action: string, row: EntryRow) {
  errorMessage.value = ''
  try {
    const result = await applyAction(meta.key, Number(row.id), action)
    if (!result.ok) throw new Error(result.message)
    await reload()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '操作失败'
  }
}

async function reload() {
  errorMessage.value = ''
  try {
    const payload = await listEntries(meta.key, filters.value)
    rows.value = payload.items
    total.value = payload.total
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '业务列表读取失败'
  }
}

// ---------- 跨模块快照 ----------
const crossSnapshot = ref<any>(null)

function computeTotalPower(electricals: any[]): number {
  let total = 0
  for (const e of electricals) {
    const power = parseFloat(String(e['额定功率'] || '0').replace('kW', '').replace('W', ''))
    if (!isNaN(power)) total += power
  }
  return total
}

async function loadCrossSnapshot() {
  // 只在展位相关视图展示跨模块面板
  if (meta.key === 'booth') {
    const boothNos = rows.value.map((r: any) => r['展位编号']).filter(Boolean)
    if (boothNos.length > 0) {
      try {
        crossSnapshot.value = await fetchJson(`/api/exhibition/booth/${boothNos[0]}/cross-snapshot`)
      } catch {
        crossSnapshot.value = null
      }
    }
  }
}

watch(() => rows.value, () => {
  void loadCrossSnapshot()
}, { deep: true })

onMounted(async () => {
  await reload()
  await loadCrossSnapshot()
})
</script>

<style scoped>
.cross-module-panel {
  margin-top: 24px;
  padding: 16px;
  border: 1px solid var(--border-color, #e0e0e0);
  border-radius: 8px;
  background: var(--bg-card, #fafafa);
}
.cross-module-panel h3 {
  margin: 0 0 12px;
  font-size: 16px;
  color: var(--text-primary, #333);
}
.cross-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 12px;
}
.cross-card {
  padding: 10px 12px;
  border: 1px solid var(--border-light, #e8e8e8);
  border-radius: 6px;
  background: #fff;
}
.cross-label {
  display: block;
  font-size: 11px;
  color: var(--text-secondary, #999);
  margin-bottom: 4px;
}
.cross-card strong {
  display: block;
  font-size: 14px;
  color: var(--text-primary, #333);
  margin-bottom: 2px;
}
.cross-card small {
  font-size: 11px;
  color: var(--text-secondary, #888);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
