// 老师工作台
const api = require('../../../utils/api')
const util = require('../../../utils/util')

Page({
  data: {
    teacherName: '老师',
    greeting: '下午好',
    dateStr: '',
    totalCount: 0,
    attendedCount: 0,
    attendanceRate: 0,
    recentActivities: [],
    isAdmin: false
  },

  onLoad() {
    if (!this.ensureTeacherLogin()) return
    this.initPage()
  },

  onShow() {
    if (!this.ensureTeacherLogin()) return
    this.initPage()
    this.loadAttendance()
  },

  ensureTeacherLogin() {
    const app = getApp()
    const userInfo = app.globalData.userInfo || {}
    const role = userInfo.role
    const isTeacher = app.globalData.userType === 'teacher' && !!app.globalData.token && (role === 'admin' || role === 'teacher')
    if (!isTeacher) {
      wx.redirectTo({ url: '/pages/teacher/login/login' })
      return false
    }
    return true
  },

  initPage() {
    // 问候语
    const hour = new Date().getHours()
    let greeting = '下午好'
    if (hour < 6) greeting = '夜深了'
    else if (hour < 9) greeting = '早上好'
    else if (hour < 12) greeting = '上午好'
    else if (hour < 14) greeting = '中午好'

    // 日期
    const now = new Date()
    const weekdays = ['日', '一', '二', '三', '四', '五', '六']
    const dateStr = now.getFullYear() + '年' + (now.getMonth() + 1) + '月' + now.getDate() + '日 星期' + weekdays[now.getDay()]

    // 老师姓名 + 角色
    const app = getApp()
    const userInfo = app.globalData.userInfo || {}
    const teacherName = userInfo.name || '老师'
    const isAdmin = userInfo.role === 'admin'

    this.setData({ greeting, dateStr, teacherName, isAdmin })
  },

  // 加载今日出勤
  loadAttendance() {
    api.request({ url: '/attendance/today' })
      .then((data) => {
        const total = data.total || 0
        const attended = data.checked_in ? data.checked_in.length : 0
        const rate = total > 0 ? Math.round(attended / total * 100) : 0
        this.setData({
          totalCount: total,
          attendedCount: attended,
          attendanceRate: rate,
          recentActivities: (data.checked_in || []).slice(0, 5).map(item => ({
            time: util.formatTimeShort(item.checkin_time),
            text: item.name + ' 到班了' + (item.is_makeup ? '（补签）' : '')
          }))
        })
      })
      .catch(() => {
        // 接口不通时用静态数据
        this.setData({
          totalCount: 20,
          attendedCount: 0,
          attendanceRate: 0,
          recentActivities: []
        })
      })
  },

  // 功能导航
  goPhoto() {
    wx.navigateTo({ url: '/pages/teacher/photo/photo' })
  },

  goPhotoLib() {
    wx.navigateTo({ url: '/pages/teacher/photolib/photolib' })
  },

  goAttendance() {
    wx.navigateTo({ url: '/pages/teacher/attendance/attendance' })
  },

  goHomework() {
    wx.navigateTo({ url: '/pages/teacher/homework/list/homework-list' })
  },

  goGrowth() {
    wx.navigateTo({ url: '/pages/teacher/growth/growth' })
  },

  goMeal() {
    wx.navigateTo({ url: '/pages/teacher/meal/meal' })
  },

  goStudents() {
    wx.navigateTo({ url: '/pages/teacher/student-list/student-list' })
  },

  goPayment() {
    wx.navigateTo({ url: '/pages/teacher/payment/payment' })
  },

  goNotices() {
    wx.navigateTo({ url: '/pages/teacher/notices/notices' })
  },

  goSettings() {
    wx.navigateTo({ url: '/pages/teacher/settings/settings' })
  },

  goAdmin() {
    wx.navigateTo({ url: '/pages/teacher/admin/admin' })
  },

  // 退出登录
  doLogout() {
    wx.showModal({
      title: '确认退出',
      content: '确定要退出登录吗？',
      success: (res) => {
        if (res.confirm) {
          const app = getApp()
          app.logout()
        }
      }
    })
  }
})
