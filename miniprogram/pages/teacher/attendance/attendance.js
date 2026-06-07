// 签到签退总览页
const api = require('../../../utils/api')
const util = require('../../../utils/util')

Page({
  data: {
    mode: 'checkin',
    isCheckinMode: true,
    isCheckoutMode: false,
    dateStr: '',
    checkinTabClass: 'active',
    checkoutTabClass: '',
    uncheckedSectionTitle: '未签到',
    uncheckedDescText: '点击签到',
    uncheckedActionText: '签到',
    loading: false,

    // 总览卡
    totalCount: 0,
    checkedInCount: 0,
    notCheckedInCount: 0,
    checkedOutCount: 0,
    checkinRate: '—',

    // 待处理
    pendingAction: [],

    // 列表
    checkedInList: [],
    notCheckedInList: [],

    // 补签
    showMakeup: false,
    makeupStudent: null,
    makeupTime: '',
    makeupReason: ''
  },

  onLoad() {
    this.initDate()
    this.loadData()
  },

  onShow() {
    this.loadData()
  },

  initDate() {
    const now = new Date()
    const month = util.padZero(now.getMonth() + 1)
    const day = util.padZero(now.getDate())
    this.setData({ dateStr: month + '月' + day + '日' })
  },

  loadData() {
    util.showLoading('加载中...')
    Promise.all([
      api.request({ url: '/students', data: { status: '在读' } }),
      api.request({ url: '/attendance/today' })
    ]).then(([students, attendance]) => {
      const all = students.students || students || []
      const checkedIn = attendance.checked_in || []
      const notCheckedIn = attendance.not_checked_in || []
      const totalCount = all.length || attendance.total || 0

      // 补全未签到列表
      let notChecked = notCheckedIn
      if (notChecked.length === 0 && checkedIn.length < totalCount) {
        const checkedIds = new Set(checkedIn.map(c => c.student_id))
        notChecked = all
          .filter(s => !checkedIds.has(s.id))
          .map(s => ({ student_id: s.id, name: s.name }))
      }

      // 已签退人数
      const checkedOutCount = checkedIn.filter(c => c.checkout_time).length

      // 待处理队列：签到模式下显示未签到，签退模式下显示已签到未签退
      let pendingAction = []
      if (notChecked.length > 0) {
        pendingAction.push({
          text: notChecked.length + ' 名学生未签到',
          action: 'checkin',
          count: notChecked.length
        })
      }
      const pendingCheckout = checkedIn.filter(c => !c.checkout_time)
      if (pendingCheckout.length > 0) {
        pendingAction.push({
          text: pendingCheckout.length + ' 名学生已签到未签退',
          action: 'checkout',
          count: pendingCheckout.length
        })
      }

      // 准备已签到显示
      const checkedDisplay = checkedIn.map((item) => ({
        ...item,
        initial: (item.name || '').slice(0, 1),
        checkoutText: item.checkout_time ? '已签退 ' + item.checkout_time : '点击签退'
      }))
      const notCheckedDisplay = notChecked.map((item) => ({
        ...item,
        initial: (item.name || '').slice(0, 1)
      }))

      // 今日签到率
      const checkinRate = totalCount > 0 ? Math.round((checkedDisplay.length / totalCount) * 100) + '%' : '—'

      this.setData({
        totalCount,
        checkedInCount: checkedDisplay.length,
        notCheckedInCount: notCheckedDisplay.length,
        checkedOutCount,
        checkinRate,
        pendingAction,
        checkedInList: checkedDisplay,
        notCheckedInList: notCheckedDisplay
      })
    }).catch(() => {
      util.showError('加载失败，请重试')
    }).finally(() => {
      wx.hideLoading()
    })
  },

  switchMode(e) {
    const mode = e.currentTarget.dataset.mode
    this.setData({
      mode,
      isCheckinMode: mode === 'checkin',
      isCheckoutMode: mode === 'checkout',
      checkinTabClass: mode === 'checkin' ? 'active' : '',
      checkoutTabClass: mode === 'checkout' ? 'active' : '',
      uncheckedSectionTitle: mode === 'checkin' ? '未签到' : '未签退',
      uncheckedDescText: mode === 'checkin' ? '点击签到' : '尚未签到',
      uncheckedActionText: mode === 'checkin' ? '签到' : '—'
    })
  },

  onStudentTap(e) {
    const student = e.currentTarget.dataset.student
    const checked = e.currentTarget.dataset.checked === true || e.currentTarget.dataset.checked === 'true'
    if (this.data.mode === 'checkin') {
      if (checked) return
      this.doCheckin(student)
    } else {
      if (!checked || student.checkout_time) return
      this.doCheckout(student)
    }
  },

  doCheckin(student) {
    this.setData({ loading: true })
    const now = new Date()
    const timestamp = now.toISOString()
    api.request({
      url: '/attendance/checkin',
      method: 'POST',
      data: { student_id: student.student_id, timestamp }
    }).then(() => {
      util.showSuccess(student.name + ' 签到成功')
      this.loadData()
    }).catch((err) => {
      util.showError(err.message)
    }).finally(() => {
      this.setData({ loading: false })
    })
  },

  doCheckout(student) {
    wx.showActionSheet({
      itemList: ['自己来接', '爸爸接', '妈妈接', '爷爷接', '奶奶接', '其他人接'],
      success: (res) => {
        const persons = ['自己', '爸爸', '妈妈', '爷爷', '奶奶', '其他人']
        const pickupPerson = persons[res.tapIndex]
        const now = new Date()
        const timestamp = now.toISOString()
        api.request({
          url: '/attendance/checkout',
          method: 'POST',
          data: { student_id: student.student_id, timestamp, pickup_person: pickupPerson }
        }).then(() => {
          util.showSuccess(student.name + ' 签退成功')
          this.loadData()
        }).catch((err) => {
          util.showError(err.message)
        })
      }
    })
  },

  // 补签
  onMakeupTap(e) {
    const student = e.currentTarget.dataset.student
    const now = new Date()
    const hours = util.padZero(now.getHours())
    const minutes = util.padZero(now.getMinutes())
    this.setData({
      showMakeup: true,
      makeupStudent: student,
      makeupTime: hours + ':' + minutes,
      makeupReason: ''
    })
  },

  onMakeupTimeChange(e) {
    this.setData({ makeupTime: e.detail.value })
  },

  onMakeupReasonInput(e) {
    this.setData({ makeupReason: e.detail.value })
  },

  confirmMakeup() {
    if (!this.data.makeupReason) { util.showError('请填写补签原因'); return }
    const student = this.data.makeupStudent
    const today = util.today()
    const timestamp = today + 'T' + this.data.makeupTime + ':00+08:00'
    api.request({
      url: '/attendance/makeup-checkin',
      method: 'POST',
      data: { student_id: student.student_id, timestamp, reason: this.data.makeupReason }
    }).then(() => {
      util.showSuccess('补签成功')
      this.setData({ showMakeup: false })
      this.loadData()
    }).catch((err) => {
      util.showError(err.message)
    })
  },

  cancelMakeup() {
    this.setData({ showMakeup: false })
  },

  goStudentList() {
    wx.navigateTo({ url: '/pages/teacher/student-list/student-list' })
  },

  nop() {}
})
