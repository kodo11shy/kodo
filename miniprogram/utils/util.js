/**
 * 工具函数
 */

/**
 * 格式化显示时间
 * 后端存 UTC，前端显示北京时间（UTC+8）
 */
const formatTime = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  const year = date.getFullYear()
  const month = padZero(date.getMonth() + 1)
  const day = padZero(date.getDate())
  const hour = padZero(date.getHours())
  const minute = padZero(date.getMinutes())
  return year + '年' + month + '月' + day + '日 ' + hour + ':' + minute
}

/**
 * 格式化日期（YYYY-MM-DD）
 */
const formatDate = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  const year = date.getFullYear()
  const month = padZero(date.getMonth() + 1)
  const day = padZero(date.getDate())
  return year + '-' + month + '-' + day
}

/**
 * 格式化时间（HH:mm）
 */
const formatTimeShort = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  const hour = padZero(date.getHours())
  const minute = padZero(date.getMinutes())
  return hour + ':' + minute
}

/**
 * 获取今天日期字符串 YYYY-MM-DD
 */
const today = () => {
  const date = new Date()
  // 转北京时间
  const bjt = new Date(date.getTime() + 8 * 60 * 60 * 1000)
  return bjt.toISOString().split('T')[0]
}

/**
 * 获取 N 天前/后的日期 YYYY-MM-DD
 * offset: 正数=未来，负数=过去
 */
const dateOffset = (offset) => {
  const date = new Date()
  date.setDate(date.getDate() + offset)
  const year = date.getFullYear()
  const month = padZero(date.getMonth() + 1)
  const day = padZero(date.getDate())
  return year + '-' + month + '-' + day
}

/**
 * 获取当前北京时间
 */
const nowBJ = () => {
  const date = new Date()
  return new Date(date.getTime() + 8 * 60 * 60 * 1000)
}

/**
 * 补零
 */
const padZero = (num) => {
  return num < 10 ? '0' + num : '' + num
}

/**
 * 显示成功提示
 */
const showSuccess = (msg) => {
  wx.showToast({ title: msg || '成功', icon: 'success' })
}

/**
 * 显示错误提示
 */
const showError = (msg) => {
  wx.showToast({ title: msg || '出错了', icon: 'none' })
}

/**
 * 显示加载中
 */
const showLoading = (msg) => {
  wx.showLoading({ title: msg || '加载中...', mask: true })
}

module.exports = {
  formatTime,
  formatDate,
  formatTimeShort,
  today,
  dateOffset,
  nowBJ,
  padZero,
  showSuccess,
  showError,
  showLoading
}
