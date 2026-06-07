// 家长首页 · 成长日记型
const api = require('../../../utils/api')
const util = require('../../../utils/util')

const FIXED_HOMEWORK_SUBJECTS = ['语文', '数学']

Page({
  data: {
    students: [],
    currentStudent: null,
    currentIndex: 0,
    loading: false,
    greeting: '下午好',
    // 今日动态
    todayPhotos: [],
    todayMeal: null,
    latestHomework: null,
    latestRemark: null,
    // 通知
    notices: [],
    // 联系老师
    contactWechat: '',
    contactPhone: '',
    // 通知弹窗
    showNoticeModal: false,
    selectedNotice: null
  },

  onLoad() {
    const hour = new Date().getHours()
    let greeting = '下午好'
    if (hour < 9) greeting = '早上好'
    else if (hour < 12) greeting = '上午好'
    this.setData({ greeting })
  },

  onShow() {
    this.loadData()
    this.loadNotices()
  },

  loadData() {
    this.setData({ loading: true })
    api.request({ url: '/parent/students' })
      .then((data) => {
        const list = (data.students || []).map((item) => ({
          ...item,
          initial: (item.name || '').slice(0, 1),
          gradeText: item.grade || '—',
          checkinTime: item.today_checkin || '',
          checkoutTime: item.today_checkout || ''
        }))
        this.setData({
          students: list,
          currentStudent: list[this.data.currentIndex] || null
        })
        if (list.length > 0) {
          this.loadStudentTimeline(list[this.data.currentIndex])
          this.loadTodayMeal()
        }
      })
      .catch((err) => {
        util.showError(err.message || '加载失败')
      })
      .finally(() => this.setData({ loading: false }))
  },

  loadNotices() {
    api.request({ url: '/public/homepage' })
      .then((data) => {
        this.setData({
          notices: (data.notices || []).slice(0, 3).map(n => ({
            id: n.id,
            title: n.title,
            content: n.content || '',
            notice_type: n.notice_type || ''
          })),
          contactWechat: data.contact_wechat || '',
          contactPhone: data.contact_phone || ''
        })
      })
      .catch(() => {})
  },

  // ... rest stays the same

  // 加载当前孩子的成长时间线（取照片和评语）
  loadStudentTimeline(student) {
    // 最新作业
    api.request({ url: '/parent/homework/' + student.id, data: { page: 1, page_size: 5 } })
      .then((data) => {
        const records = (data.records || []).filter(item => FIXED_HOMEWORK_SUBJECTS.includes(item.subject))
        if (records.length > 0) {
          const hw = records[0]
          const statusMap = { '待批改': 'waiting', '已批改': 'graded', '已完成': 'done' }
          this.setData({
            latestHomework: {
              id: hw.id,
              subject: hw.subject,
              statusLabel: hw.status,
              statusClass: statusMap[hw.status] || 'waiting',
              remark: hw.remark ? hw.remark.slice(0, 40) : '',
              date: hw.date || ''
            }
          })
        }
      })
      .catch(() => {})

    // 成长时间线 → 取最近照片和评语
    api.request({ url: '/parent/growth/' + student.id, data: { days: 7 } })
      .then((data) => {
        const items = data.timeline || []
        // 取照片（去重）
        const seen = new Set()
        const photos = []
        for (const item of items) {
          if (item.type === 'photo' || item.type === 'homework') {
            const p = item.photos || []
            for (const ph of p) {
              if (!seen.has(ph.id) && photos.length < 9) {
                seen.add(ph.id)
                photos.push({ id: ph.id, url: api.imageUrl(ph.file_path || ph.url) })
              }
            }
          }
        }
        this.setData({ todayPhotos: photos })

        // 取最新评语
        for (const item of items) {
          if (item.type === 'remark') {
            this.setData({
              latestRemark: {
                content: item.content || '',
                mood_tag: item.mood_tag || '',
                date: item.date || ''
              }
            })
            break
          }
        }
      })
      .catch(() => {})
  },

  // 加载最新餐食
  loadTodayMeal() {
    api.request({ url: '/meals', data: { page: 1, page_size: 1 } })
      .then((data) => {
        const records = data.records || data.meals || []
        if (records.length > 0) {
          this.setData({ todayMeal: records[0] })
        }
      })
      .catch(() => {})
  },

  switchStudent(e) {
    const idx = e.currentTarget.dataset.index
    const student = this.data.students[idx]
    this.setData({
      currentIndex: idx,
      currentStudent: student || null,
      todayPhotos: [],
      todayMeal: null,
      latestHomework: null,
      latestRemark: null
    })
    if (student) {
      this.loadStudentTimeline(student)
    }
  },

  previewPhoto(e) {
    const url = e.currentTarget.dataset.url
    wx.previewImage({ urls: [url] })
  },

  goGrowth() {
    const s = this.data.currentStudent
    if (!s) return
    wx.navigateTo({ url: '/pages/parent/growth/growth?student_id=' + s.id + '&name=' + encodeURIComponent(s.name) })
  },

  goHomework() {
    const s = this.data.currentStudent
    if (!s) return
    wx.navigateTo({ url: '/pages/parent/homework/homework?student_id=' + s.id + '&name=' + encodeURIComponent(s.name) })
  },

  goPhotos() {
    const s = this.data.currentStudent
    if (!s) return
    wx.navigateTo({ url: '/pages/parent/photos/photos?student_id=' + s.id + '&name=' + encodeURIComponent(s.name) })
  },

  tapNotice(e) {
    const id = e.currentTarget.dataset.id
    const notice = this.data.notices.find(n => n.id === id)
    if (notice && notice.content) {
      this.setData({ showNoticeModal: true, selectedNotice: notice })
    }
  },

  closeNotice() {
    this.setData({ showNoticeModal: false, selectedNotice: null })
  },

  copyWechat() {
    const w = this.data.contactWechat
    if (w) {
      wx.setClipboardData({
        data: w,
        success: () => wx.showToast({ title: '微信号已复制', icon: 'success' })
      })
    }
  },

  callPhone() {
    const p = this.data.contactPhone
    if (p) wx.makePhoneCall({ phoneNumber: p })
  },

  doLogout() {
    wx.showModal({
      title: '退出登录',
      content: '确定要退出吗？',
      success: (res) => {
        if (res.confirm) {
          wx.removeStorageSync('token')
          wx.removeStorageSync('userType')
          wx.reLaunch({ url: '/pages/index/index' })
        }
      }
    })
  }
})
