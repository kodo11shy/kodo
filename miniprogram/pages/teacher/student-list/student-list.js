// 学生管理总览页
const api = require('../../../utils/api')
const util = require('../../../utils/util')

Page({
  data: {
    allStudents: [],
    students: [],
    filters: [],
    activeFilter: 'all',
    keyword: '',
    loading: false,
    total: 0,
    checkedInCount: 0,
    absentCount: 0,
    parentBoundText: '0/0',
    completeText: '0/0',
    issueCount: 0,
    issueSummary: [],
    emptyTitle: '还没有学生',
    emptyDesc: '请先录入学生和家长信息'
  },

  onLoad() {
    this.loadOverview()
  },

  onShow() {
    this.loadOverview()
  },

  loadOverview() {
    this.setData({ loading: true })
    const params = { status: '在读' }
    if (this.data.keyword) params.keyword = this.data.keyword

    Promise.all([
      api.request({ url: '/students', data: params }),
      api.request({ url: '/attendance/today' }).catch(() => ({ checked_in: [], total: 0 }))
    ]).then(([studentData, attendanceData]) => {
      const basicStudents = studentData.students || studentData || []
      const checkedIn = attendanceData.checked_in || []
      const checkedInIds = checkedIn.map(item => item.student_id || item.id)

      return Promise.all(
        basicStudents.map(student =>
          api.request({ url: '/students/' + student.id })
            .then(detail => ({ ...student, ...detail }))
            .catch(() => student)
        )
      ).then(details => {
        const students = details.map(item => this._buildStudentRow(item, checkedInIds))
        this._setOverview(students, checkedInIds.length)
      })
    }).catch(() => {
      util.showError('加载失败')
      this.setData({ allStudents: [], students: [] })
    }).finally(() => {
      this.setData({ loading: false })
    })
  },

  _buildStudentRow(item, checkedInIds) {
    const parents = item.parents || []
    const pickups = item.pickups || []
    const health = item.health || {}
    const parentBound = parents.some(parent => parent.wechat_bound)
    const checkedIn = checkedInIds.includes(item.id)
    const issues = []

    if (parents.length === 0) issues.push('缺家长')
    if (parents.length > 0 && !parentBound) issues.push('家长未绑定')
    if (pickups.length === 0) issues.push('缺接送人')
    if (!health.consent_signed) issues.push('健康未确认')
    if (!item.grade || !item.school_name || !item.school_class || !item.address) {
      issues.push('基础资料待补')
    }

    const tags = [
      {
        text: checkedIn ? '已到' : '未到',
        className: checkedIn ? 'ok' : 'muted'
      },
      {
        text: parentBound ? '家长已绑' : '家长未绑',
        className: parentBound ? 'ok' : 'warn'
      },
      {
        text: issues.length === 0 ? '资料完整' : '待补' + issues.length,
        className: issues.length === 0 ? 'ok' : 'danger'
      }
    ]

    return {
      ...item,
      initial: (item.name || '').slice(0, 1),
      detailText: (item.grade || '—') + ' · ' + (item.school_name || '—') + ' · ' + (item.school_class || '—'),
      checkedIn,
      parentBound,
      profileComplete: issues.length === 0,
      issues,
      issueText: issues.length > 0 ? issues.join('、') : '资料完整',
      tags
    }
  },

  _setOverview(students, checkedInCount) {
    const total = students.length
    const absentCount = students.filter(item => !item.checkedIn).length
    const parentTotal = students.reduce((sum, item) => sum + (item.parents || []).length, 0)
    const parentBoundTotal = students.reduce((sum, item) => {
      return sum + (item.parents || []).filter(parent => parent.wechat_bound).length
    }, 0)
    const completeCount = students.filter(item => item.profileComplete).length
    const issueStudents = students.filter(item => item.issues.length > 0)

    const healthMissing = students.filter(item => item.issues.includes('健康未确认')).length
    const unbound = students.filter(item => item.issues.includes('家长未绑定')).length
    const pickupMissing = students.filter(item => item.issues.includes('缺接送人')).length
    const baseMissing = students.filter(item => item.issues.includes('基础资料待补')).length
    const issueSummary = [
      { label: '健康告知未确认', count: healthMissing },
      { label: '家长未绑定微信', count: unbound },
      { label: '缺默认接送人', count: pickupMissing },
      { label: '基础资料待补', count: baseMissing }
    ].filter(item => item.count > 0)

    const filters = [
      { key: 'all', label: '全部', count: total },
      { key: 'present', label: '今日在托', count: checkedInCount },
      { key: 'absent', label: '未到', count: absentCount },
      { key: 'issues', label: '资料待补', count: issueStudents.length },
      { key: 'unbound', label: '家长未绑定', count: unbound }
    ]

    this.setData({
      allStudents: students,
      total,
      checkedInCount,
      absentCount,
      parentBoundText: parentBoundTotal + '/' + parentTotal,
      completeText: completeCount + '/' + total,
      issueCount: issueStudents.length,
      issueSummary,
      filters
    })
    this._applyFilter()
  },

  _applyFilter() {
    const filter = this.data.activeFilter
    let students = this.data.allStudents
    if (filter === 'present') students = students.filter(item => item.checkedIn)
    if (filter === 'absent') students = students.filter(item => !item.checkedIn)
    if (filter === 'issues') students = students.filter(item => item.issues.length > 0)
    if (filter === 'unbound') students = students.filter(item => item.issues.includes('家长未绑定'))

    const emptyMap = {
      all: ['还没有学生', '请先录入学生和家长信息'],
      present: ['今天还没有学生到班', '签到后会显示今日在托学生'],
      absent: ['没有未到学生', '今天所有学生都已到班'],
      issues: ['暂无待补资料', '学生档案、接送和健康信息都已完整'],
      unbound: ['暂无未绑定家长', '家长绑定状态都正常']
    }
    const empty = emptyMap[filter] || emptyMap.all
    this.setData({ students, emptyTitle: empty[0], emptyDesc: empty[1] })
  },

  switchFilter(e) {
    const filter = e.currentTarget.dataset.filter
    if (filter === this.data.activeFilter) return
    this.setData({ activeFilter: filter })
    this._applyFilter()
  },

  onSearchInput(e) {
    this.setData({ keyword: e.detail.value })
  },

  onSearch() {
    this.loadOverview()
  },

  onClearSearch() {
    this.setData({ keyword: '' })
    this.loadOverview()
  },

  goDetail(e) {
    const id = e.currentTarget.dataset.id
    wx.navigateTo({ url: '/pages/teacher/student-detail/student-detail?id=' + id })
  },

  goAttendance() {
    wx.navigateTo({ url: '/pages/teacher/attendance/attendance' })
  },

  goAdd() {
    wx.showToast({ title: '请在系统管理中添加学生', icon: 'none' })
  }
})
