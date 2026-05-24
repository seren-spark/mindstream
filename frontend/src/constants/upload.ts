export const ALLOWED_UPLOAD_EXTENSIONS = ['.pdf', '.docx', '.doc', '.md', '.markdown', '.txt']

export const ALLOWED_UPLOAD_ACCEPT = ALLOWED_UPLOAD_EXTENSIONS.join(',')

export const MAX_UPLOAD_SIZE_MB = 20

export const MAX_UPLOAD_COUNT = 10

export const UPLOAD_STATUS_LABEL: Record<string, string> = {
  idle: '待上传',
  queued: '排队中',
  uploading: '上传中',
  parsing: '解析中',
  success: '完成',
  error: '失败',
}

export function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

export function validateLocalFile(file: File): string | null {
  const name = file.name.toLowerCase()
  const allowed = ALLOWED_UPLOAD_EXTENSIONS.some((ext) => name.endsWith(ext))
  if (!allowed) {
    return `不支持的格式，仅支持 ${ALLOWED_UPLOAD_EXTENSIONS.join(' / ')}`
  }
  if (file.size <= 0) return '文件为空'
  if (file.size > MAX_UPLOAD_SIZE_MB * 1024 * 1024) {
    return `文件超过 ${MAX_UPLOAD_SIZE_MB} MB 限制`
  }
  return null
}

export function getFileExtension(filename: string): string {
  const index = filename.lastIndexOf('.')
  return index >= 0 ? filename.slice(index + 1).toLowerCase() : ''
}
