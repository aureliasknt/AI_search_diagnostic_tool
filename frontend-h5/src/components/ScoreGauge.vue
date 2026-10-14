<template>
  <div ref="el" class="gauge" :style="{ height: size + 'px' }"></div>
</template>

<script setup>
import { onMounted, onBeforeUnmount, ref, watch } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  score: { type: Number, default: 0 },
  size: { type: Number, default: 230 },
})

const el = ref(null)
let chart = null

function render() {
  if (!chart) return
  const v = Math.max(0, Math.min(100, props.score))
  chart.setOption({
    series: [{
      type: 'gauge',
      startAngle: 200,
      endAngle: -20,
      min: 0,
      max: 100,
      radius: '100%',
      center: ['50%', '62%'],
      progress: {
        show: true,
        width: 16,
        roundCap: true,
        itemStyle: {
          color: {
            type: 'linear', x: 0, y: 0, x2: 1, y2: 0,
            colorStops: [
              { offset: 0, color: '#6d28d9' },
              { offset: 1, color: '#c084fc' },
            ],
          },
          shadowColor: 'rgba(139,92,246,.45)',
          shadowBlur: 12,
        },
      },
      axisLine: {
        lineStyle: {
          width: 16,
          color: [[1, '#efe9fb']],
        },
      },
      axisTick: { show: false },
      splitLine: { show: false },
      axisLabel: { show: false },
      pointer: { show: false },
      anchor: { show: false },
      detail: {
        valueAnimation: true,
        offsetCenter: [0, '-14%'],
        fontSize: 44,
        fontWeight: 800,
        color: '#5b21b6',
        formatter: (val) => val.toFixed(2),
      },
      title: { show: false },
      data: [{ value: v }],
    }],
  })
}

onMounted(() => {
  chart = echarts.init(el.value)
  render()
  window.addEventListener('resize', render)
})
watch(() => props.score, render)
onBeforeUnmount(() => {
  window.removeEventListener('resize', render)
  chart && chart.dispose()
})
</script>

<style scoped>
.gauge { width: 100%; }
</style>
