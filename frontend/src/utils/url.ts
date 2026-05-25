/**
 * 将后端返回的文件 URL（如 /uploads/xxx）解析为浏览器可访问的完整地址。
 *
 * 开发环境：Vite 代理 /uploads 到后端，相对路径即可工作，无需处理。
 * 生产环境：通过 VITE_API_BASE 环境变量指定后端地址，拼接为绝对 URL。
 */
export function resolveFileUrl(url: string | undefined | null): string {
  if (!url) return ''
  if (/^https?:\/\//i.test(url)) return url
  const base = import.meta.env.VITE_API_BASE as string | undefined
  if (!base) return url
  return `${base.replace(/\/$/, '')}${url}`
}
