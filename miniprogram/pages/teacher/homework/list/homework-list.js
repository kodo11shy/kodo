// 作业列表页 — 总览所有作业，按状态筛选
const app = getApp()
const api = require('../../../../utils/api')
const util = require('../../../../utils/util')

const SUBJECT_ICONS = {
  '语文': '📖', '数学': '🔢',
}
const FIXED_HOMEWORK_SUBJECTS = ['语文', '数学']

Page({
  data: {
    loading: false,
    activeTab: 'all',
    records: [],
    filteredList: [],
    studentMap: {},
    // 当前老师信息
    teacherSubject: '',
    isAdmin: false,
    // 总览数据
    totalStudents: 0,
    attendanceCount: 0,
    attendanceNames: '',
    subjectStats: [],
    // 状态说明
    showStatusHint: false,
  },

  onLoad() {
    // 读取当前老师信息
    const userInfo = app.globalData.userInfo || {}
    this.setData({
      teacherSubject: userInfo.subject || '',
      isAdmin: userInfo.role === 'admin'
    })
    this.loadStudents()
    this.loadAttendance()
    this.loadRecords()
  },

  onShow() {
    this.loadAttendance()
    this.loadRecords(true)
  },

  onPullDownRefresh() {
    Promise.all([
      this.loadRecords(true),
      this.loadAttendance()
    ]).finally(() => wx.stopPullDownRefresh())
  },

  loadStudents() {
    api.request({ url: '/students', data: { status: '在读' } })
      .then((data) => {
        const map = {}
        const list = data.students || data || []
        list.forEach(s => { map[s.id] = s.name })
        this.setData({ studentMap: map })
        // 重新格式化已有记录（更新学生姓名）
        if (this.data.records.length > 0) {
          const records = this.data.records.map(r => this._formatRecord(r))
          this.setData({ records })
          this._applyFilter()
        }
      })
      .catch(() => {})
  },

  loadAttendance() {
    return api.request({ url: '/attendance/today' })
      .then((data) => {
        const checkedIn = data.checked_in || []
        const names = checkedIn.map(s => s.name)
        this.setData({
          totalStudents: data.total || 0,
          attendanceCount: checkedIn.length,
          attendanceNames: names.join('、')
        })
      })
      .catch(() => {
        this.setData({ totalStudents: 0, attendanceCount: 0, attendanceNames: '' })
      })
  },

  loadRecords(refresh) {
    if (refresh) this.setData({ records: [] })
    this.setData({ loading: true })

    // 构造请求参数：非管理员老师只拉自己学科的作业
    const params = { page: 1, page_size: 100 }
    if (!this.data.isAdmin && this.data.teacherSubject) {
      params.subject = this.data.teacherSubject
    }

    return api.request({ url: '/homework', data: params })
      .then((data) => {
        const records = (data.records || [])
          .filter(r => FIXED_HOMEWORK_SUBJECTS.includes(r.subject))
          .map(r => this._formatRecord(r))
        this.setData({ records })
        this._applyFilter()
        this._calcSubjectStats(records)
      })
      .catch(() => {
        util.showError('加载失败')
      })
      .finally(() => {
        this.setData({ loading: false })
      })
  },

  _calcSubjectStats(records) {
    const stats = {}
    FIXED_HOMEWORK_SUBJECTS.forEach(subject => {
      stats[subject] = { subject, icon: SUBJECT_ICONS[subject], total: 0, pending: 0, graded: 0, done: 0 }
    })
    for (const r of records) {
      const sub = r.subject
      if (!FIXED_HOMEWORK_SUBJECTS.includes(sub)) continue
      stats[sub].total++
      if (r.status === '待批改') stats[sub].pending++
      else if (r.status === '已批改') stats[sub].graded++
      else if (r.status === '已完成') stats[sub].done++
    }
    const subjectStats = FIXED_HOMEWORK_SUBJECTS.map(subject => stats[subject]).map(item => {
      const total = item.total || 0
      return {
        ...item,
        pendingWidth: total > 0 ? (item.pending / total * 100) : 0,
        gradedWidth: total > 0 ? (item.graded / total * 100) : 0,
        doneWidth: total > 0 ? (item.done / total * 100) : 0,
      }
    })
    this.setData({ subjectStats })
  },

  _formatRecord(r) {
    const classMap = { '待批改': 'pending', '已批改': 'graded', '已完成': 'done' }
    const labelMap = { '待批改': '⏳ 待批改', '已批改': '✅ 已批改', '已完成': '🎉 已完成' }

    const photos = {}
    if (r.photos) {
      for (const step of ['done', 'graded', 'corrected']) {
        photos[step] = (r.photos[step] || []).map(p => ({
          ...p,
          url: api.imageUrl(p.file_path)
        }))
      }
    }

    // 构建操作人信息
    let operatorInfo = ''
    if (r.status === '已批改' && r.graded_by_name) {
      operatorInfo = `批改：${r.graded_by_name}`
      if (r.graded_at) operatorInfo += ` ${util.formatTime(r.graded_at)}`
    } else if (r.status === '已完成' && r.corrected_by_name) {
      operatorInfo = `改错：${r.corrected_by_name}`
      if (r.corrected_at) operatorInfo += ` ${util.formatTime(r.corrected_at)}`
      if (r.graded_by_name) operatorInfo = `批改：${r.graded_by_name} | 改错：${r.corrected_by_name}`
    }

    return {
      id: r.id,
      studentId: r.student_id,
      studentName: r.student_name || this.data.studentMap[r.student_id] || '学生#' + r.student_id,
      subject: r.subject,
      homeworkType: r.homework_type || '',
      status: r.status,
      statusLabel: labelMap[r.status] || r.status,
      statusClass: classMap[r.status] || 'pending',
      score: r.score,
      errorCount: r.error_count,
      accuracy: r.accuracy,
      remark: r.remark,
      date: r.date || '',
      completedAt: r.completed_at,
      photos,
      donePhotoThumbs: (photos.done || []).slice(0, 4),
      operatorInfo
    }
  },

  _applyFilter() {
    const tab = this.data.activeTab
    let filtered = this.data.records
    if (tab !== 'all') {
      filtered = this.data.records.filter(r => r.status === tab)
    }
    this.setData({ filteredList: filtered })
  },

  switchTab(e) {
    const tab = e.currentTarget.dataset.tab
    if (tab === this.data.activeTab) return
    this.setData({ activeTab: tab })
    this._applyFilter()
  },

  goDetail(e) {
    const id = e.currentTarget.dataset.id
    wx.navigateTo({
      url: '/pages/teacher/homework/detail/homework-detail?id=' + id
    })
  },

  goCreate() {
    wx.navigateTo({
      url: '/pages/teacher/homework/create/homework-create'
    })
  },

  toggleStatusHint() {
    this.setData({ showStatusHint: !this.data.showStatusHint })
  }
})
