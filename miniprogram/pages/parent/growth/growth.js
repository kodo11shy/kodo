// 家长端成长档案
const api = require('../../../utils/api')
const util = require('../../../utils/util')

Page({
  data: {
    studentId: 0,
    studentName: '',
    overview: null,
    overviewGrade: '',
    attendedDays: 0,
    avgScore: '—',
    homeworkCount: 0,
    timeline: [],
    showReport: false,
    loading: false
  },

  onLoad(options) {
    const studentId = parseInt(options.student_id || 0)
    const name = decodeURIComponent(options.name || '孩子')
    this.setData({ studentId, studentName: name })
    if (studentId) this.loadData()
  },

  onShow() {
    if (this.data.studentId) this.loadData()
  },

  loadData() {
    this.setData({ loading: true })
    api.request({ url: '/parent/growth/' + this.data.studentId })
      .then((data) => {
        const overview = data.overview || null
        const current = overview && overview.current_month ? overview.current_month : {}
        const studentInfo = overview && overview.student_info ? overview.student_info : {}
        const timeline = (data.timeline || []).map((item) => ({
          ...item,
          icon: this.getTypeIcon(item.type),
          displayTitle: item.title || item.type,
          displayDate: util.formatDate(item.date)
        }))
        this.setData({
          overview,
          overviewGrade: studentInfo.grade || '',
          attendedDays: current.attended_days || 0,
          avgScore: current.avg_score || '—',
          homeworkCount: current.homework_count || 0,
          timeline
        })
      })
      .catch(() => util.showError('加载失败'))
      .finally(() => this.setData({ loading: false }))
  },

  // 保存成长报告（引导截图）
  saveReport() {
    wx.showModal({
      title: '📥 保存成长报告',
      content: '将展示成长报告卡片，请截屏保存。',
      confirmText: '查看报告',
      success: (res) => {
        if (res.confirm) {
          this.setData({ showReport: true })
        }
      }
    })
  },

  closeReport() {
    this.setData({ showReport: false })
  },

  // 时间线类型图标
  getTypeIcon(type) {
    const icons = { homework: '📚', remark: '📝', meal: '🍱', milestone: '🏆', photo: '📸' }
    return icons[type] || '📌'
  },

  // 展示字段在 JS 中提前整理，避免 WXML 使用不兼容表达式。
})
