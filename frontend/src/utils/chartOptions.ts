import type { TrendPoint, HeatItem } from '@/types/stats'
import type { EChartsOption } from 'echarts'

export function buildTrendOption(points: TrendPoint[]): EChartsOption {
  const dates = points.map((p) => p.date.slice(5))
  const counts = points.map((p) => p.question_count)

  return {
    grid: { left: 48, right: 24, top: 36, bottom: 32 },
    tooltip: {
      trigger: 'axis',
      formatter: (params: unknown) => {
        const row = (params as { name: string; value: number }[])[0]
        if (!row) return ''
        return `${row.name}<br/>提问 ${row.value} 次`
      },
    },
    xAxis: {
      type: 'category',
      data: dates,
      axisLine: { lineStyle: { color: '#E5E6EB' } },
      axisLabel: { color: '#86909C' },
    },
    yAxis: {
      type: 'value',
      minInterval: 1,
      splitLine: { lineStyle: { type: 'dashed', color: '#F2F3F5' } },
      axisLabel: { color: '#86909C' },
    },
    series: [
      {
        name: '提问量',
        type: 'line',
        smooth: 0.35,
        symbol: 'circle',
        symbolSize: 6,
        lineStyle: { width: 2.5, color: 'rgb(var(--primary-6))' },
        itemStyle: { color: 'rgb(var(--primary-6))' },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(var(--primary-6), 0.18)' },
              { offset: 1, color: 'rgba(var(--primary-6), 0.02)' },
            ],
          },
        },
        data: counts,
      },
    ],
  }
}

export function buildHeatOption(items: HeatItem[]): EChartsOption {
  const titles = [...items].reverse().map((i) => i.title)
  const values = [...items].reverse().map((i) => i.cite_count)

  return {
    grid: { left: 8, right: 48, top: 8, bottom: 8, containLabel: true },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter: (params: unknown) => {
        const row = (params as { name: string; value: number }[])[0]
        if (!row) return ''
        return `${row.name}<br/>被引用 ${row.value} 次`
      },
    },
    xAxis: { type: 'value', show: false },
    yAxis: {
      type: 'category',
      data: titles,
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: {
        width: 110,
        overflow: 'truncate',
        color: '#4E5969',
      },
    },
    series: [
      {
        type: 'bar',
        barWidth: 14,
        itemStyle: {
          borderRadius: [0, 6, 6, 0],
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 1,
            y2: 0,
            colorStops: [
              { offset: 0, color: 'rgba(var(--primary-6), 0.85)' },
              { offset: 1, color: 'rgba(var(--primary-6), 0.45)' },
            ],
          },
        },
        label: { show: true, position: 'right', color: '#86909C', fontSize: 11 },
        data: values,
      },
    ],
  }
}
