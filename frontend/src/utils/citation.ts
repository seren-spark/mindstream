import type { CitationRef } from '@/types/chat'

/** 将正文 [n] 转为可点击锚点（Markdown 链接） */
export function linkifyCitationMarkers(content: string, citations?: CitationRef[]): string {
  if (!citations?.length) return content
  const valid = new Set(citations.map((c) => c.index))
  return content.replace(/\[(\d{1,2})\]/g, (full, raw) => {
    const index = Number(raw)
    if (!valid.has(index)) return full
    return `[${index}](#cite-${index})`
  })
}

export function getCitationLabel(cite: CitationRef): string {
  return cite.display_title || cite.source_name || `条目 #${cite.knowledge_item_id}`
}

export function getCitationSnippet(cite: CitationRef): string {
  return cite.highlight_text?.trim() || cite.content_excerpt?.trim() || ''
}

export function getCitationLocation(cite: CitationRef): string {
  const loc = cite.source_location
  const parts: string[] = []
  if (loc.page_start != null) {
    parts.push(
      loc.page_end != null && loc.page_end !== loc.page_start
        ? `第 ${loc.page_start}-${loc.page_end} 页`
        : `第 ${loc.page_start} 页`,
    )
  }
  if (loc.section_title) parts.push(loc.section_title)
  if (loc.heading_path?.length) parts.push(loc.heading_path.join(' › '))
  return parts.join(' · ')
}

export function formatCitationDate(iso?: string | null): string {
  if (!iso) return ''
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return ''
  return `${d.getFullYear()}-${d.getMonth() + 1}-${d.getDate()}`
}
