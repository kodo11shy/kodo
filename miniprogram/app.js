const config = require('./config')

App({
  globalData: {
    userInfo: null,
    userType: '',
    studentIds: [],
    token: '',
    apiBase: config.apiBase,
    apiOrigin: config.apiOrigin,
    apiFallbackBase: config.apiFallbackBase,
    apiFallbackOrigin: config.apiFallbackOrigin
  },

  onLaunch() {
    // 只持久恢复家长端登录。老师端每次重新进入都要求输入密码，避免托班后台被缓存绕过。
    const token = wx.getStorageSync('token')
    const userType = wx.getStorageSync('userType')
    if (token && userType === 'parent') {
      this.globalData.token = token
      this.globalData.userType = 'parent'
      this.globalData.studentIds = wx.getStorageSync('studentIds') || []
    } else {
      wx.removeStorageSync('token')
      wx.removeStorageSync('userInfo')
      wx.removeStorageSync('userType')
      wx.removeStorageSync('studentIds')
    }
  },

  // 全局登录方法
  login(password) {
    return new Promise((resolve, reject) => {
      const send = (apiBase, retried = false) => wx.request({
        url: apiBase + '/auth/teacher/login',
        method: 'POST',
        data: { password },
        timeout: 15000,
        success: (res) => {
          if (res.data.code === 0) {
            const { token, teacher } = res.data.data
            this.globalData.token = token
            this.globalData.userInfo = teacher
            this.globalData.userType = 'teacher'
            this.globalData.studentIds = []
            wx.removeStorageSync('token')
            wx.removeStorageSync('userInfo')
            wx.removeStorageSync('userType')
            wx.removeStorageSync('studentIds')
            resolve(teacher)
          } else {
            reject(new Error(res.data.message || '登录失败'))
          }
        },
        fail: (err) => {
          console.error('登录请求失败', apiBase + '/auth/teacher/login', err)
          if (!retried && this.globalData.apiFallbackBase && apiBase !== this.globalData.apiFallbackBase) {
            send(this.globalData.apiFallbackBase, true)
            return
          }
          reject(new Error('网络错误：' + err.errMsg))
        }
      })

      send(this.globalData.apiBase)
    })
  },

  // 全局退出
  logout() {
    this.globalData.token = ''
    this.globalData.userInfo = null
    this.globalData.userType = ''
    this.globalData.studentIds = []
    wx.removeStorageSync('token')
    wx.removeStorageSync('userInfo')
    wx.removeStorageSync('userType')
    wx.removeStorageSync('studentIds')
    wx.reLaunch({ url: '/pages/index/index' })
  }
})
