// 老师端成长档案总览
const api = require('../../../utils/api')
const util = require('../../../utils/util')

Page({
  data: {
    students: [],
    studentsWithGrowth: [],
    loading: false,

    // 总览卡
    studentCount: 0,
    totalHomework: 0,
    totalRemarks: 0,
    avgScore: '—',

    // 选中学生详情
    studentId: 0,
    selectedStudent: null,
    overview: null,
    attendedDays: 0,
    homeworkCount: 0,
    remarkCount: 0,

    showDetail: false,

    // 时间线
    timeline: [],

    // 评语
    showRemarkInput: false,
    remarkContent: '',
    canSubmitRemark: false,
    remarkSubmitDisabled: true,
    remarkMood: '开心',
    moodOptions: [
      { mood: '开心', label: '😊 开心', className: 'active' },
      { mood: '进步', label: '📈 进步', className: '' },
      { mood: '鼓励', label: '💪 鼓励', className: '' },
      { mood: '注意', label: '⚠️ 注意', className: '' }
    ],
    submitting: false
  },

  onLoad() {
    this.loadOverview()
  },

  onShow() {
    if (!this.data.showDetail) this.loadOverview()
  },

  loadOverview() {
    this.setData({ loading: true, showDetail: false })

    api.request({ url: '/students', data: { status: '在读' } })
      .then((data) => {
        const list = data.students || []
        this.setData({ students: list, studentCount: list.length })

        // 逐个取 growth overview
        return Promise.all(list.map(student =>
          api.request({ url: '/growth/overview/' + student.id })
            .then(ov => ({ ...student, overview: ov }))
            .catch(() => ({ ...student, overview: null }))
        ))
      })
      .then((studentsWithGrowth) => {
        // 汇总全班数据
        let totalHw = 0, totalRm = 0, totalScore = 0, scoreCount = 0
        studentsWithGrowth.forEach(s => {
          const cur = s.overview?.current_month || {}
          totalHw += cur.homework_count || 0
          totalRm += cur.remark_count || 0
          if (cur.avg_score) { totalScore += parseFloat(cur.avg_score); scoreCount++ }
        })

        // 构建学生卡片
        const avatarColors = ['#5B7FFF', '#FF8C5A', '#36C2A0', '#FF6B6B', '#A77BFF', '#FFB347']
        const list = studentsWithGrowth.map((s, idx) => {
          const cur = s.overview?.current_month || {}
          const latestRemark = s.overview?.latest_remark || ''
          return {
            ...s,
            initial: (s.name || '').slice(0, 1),
            avatarColor: avatarColors[idx % avatarColors.length],
            detailText: s.grade || '—',
            hwCount: cur.homework_count || 0,
            rmCount: cur.remark_count || 0,
            attendedDays: cur.attended_days || 0,
            attendedPct: Math.min(100, Math.round(((cur.attended_days || 0) / 22) * 100)),
            avgScoreStr: cur.avg_score || '—',
            latestRemark: latestRemark.toString().slice(0, 24) + (latestRemark.length > 24 ? '...' : '')
          }
        })

        this.setData({
          studentsWithGrowth: list,
          totalHomework: totalHw,
          totalRemarks: totalRm,
          avgScore: scoreCount > 0 ? (totalScore / scoreCount).toFixed(1) : '—'
        })
      })
      .catch(() => util.showError('加载失败'))
      .finally(() => this.setData({ loading: false }))
  },

  goDetail(e) {
    const studentId = parseInt(e.currentTarget.dataset.id)
    const student = this.data.studentsWithGrowth.find(s => s.id === studentId)
    if (!student) return

    // 为详情模式也加上 avatarColor
    if (!student.avatarColor) {
      const colors = ['#5B7FFF', '#FF8C5A', '#36C2A0', '#FF6B6B', '#A77BFF', '#FFB347']
      student.avatarColor = colors[studentId % colors.length]
    }
    if (!student) return

    this.setData({
      studentId,
      selectedStudent: student,
      showDetail: true,
      overview: student.overview || null,
      attendedDays: student.overview?.current_month?.attended_days || 0,
      homeworkCount: student.overview?.current_month?.homework_count || 0,
      remarkCount: student.overview?.current_month?.remark_count || 0,
      timeline: []
    })
    this.loadTimeline()
  },

  loadTimeline() {
    if (!this.data.studentId) return
    api.request({ url: '/growth/timeline/' + this.data.studentId, data: { days: 30 } })
      .then((data) => {
        const timeline = (data.timeline || []).map((item) => ({
          ...item,
          icon: this.getTypeIcon(item.type),
          displayTitle: item.title || item.type
        }))
        this.setData({ timeline })
      })
      .catch(() => util.showError('加载时间线失败'))
  },

  backToList() {
    this.setData({ showDetail: false, selectedStudent: null, timeline: [] })
    this.loadOverview()
  },

  // 评语
  openRemark() {
    this.setData({
      showRemarkInput: true,
      remarkContent: '',
      canSubmitRemark: false,
      remarkSubmitDisabled: true,
      remarkMood: '开心',
      moodOptions: this._buildMoodOptions('开心')
    })
  },

  closeRemark() {
    this.setData({ showRemarkInput: false })
  },

  onRemarkInput(e) {
    const canSubmitRemark = !!(e.detail.value || '').trim()
    this.setData({
      remarkContent: e.detail.value,
      canSubmitRemark,
      remarkSubmitDisabled: this.data.submitting || !canSubmitRemark
    })
  },

  selectMood(e) {
    const mood = e.currentTarget.dataset.mood
    this.setData({ remarkMood: mood, moodOptions: this._buildMoodOptions(mood) })
  },

  _buildMoodOptions(activeMood) {
    return [
      { mood: '开心', label: '😊 开心' },
      { mood: '进步', label: '📈 进步' },
      { mood: '鼓励', label: '💪 鼓励' },
      { mood: '注意', label: '⚠️ 注意' }
    ].map(item => ({ ...item, className: item.mood === activeMood ? 'active' : '' }))
  },

  submitRemark() {
    if (!this.data.remarkContent.trim()) { util.showError('请填写评语内容'); return }
    this.setData({ submitting: true, remarkSubmitDisabled: true })
    const today = util.today()
    api.request({
      url: '/remarks',
      method: 'POST',
      data: {
        student_id: this.data.studentId,
        record_date: today,
        content: this.data.remarkContent,
        mood_tag: this.data.remarkMood
      }
    }).then(() => {
      util.showSuccess('评语已保存')
      this.setData({ showRemarkInput: false })
      this.loadTimeline()
    }).catch((err) => {
      util.showError(err.message || '保存失败')
    }).finally(() => {
      const canSubmitRemark = this.data.canSubmitRemark
      this.setData({ submitting: false, remarkSubmitDisabled: !canSubmitRemark })
    })
  },

  getTypeIcon(type) {
    const icons = { homework: '📚', remark: '📝', meal: '🍱', milestone: '🏆', photo: '📸' }
    return icons[type] || '📌'
  }
})
