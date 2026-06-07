// 首页（家长信任型）
const api = require('../../utils/api')
const util = require('../../utils/util')

Page({
  data: {
    schoolName: '智慧托班',
    welcomeMessage: '用心陪伴每一个孩子',
    contactWechat: '',
    contactPhone: '',
    notices: [],
    latestNotice: null,
    feeStandard: [],
    featuredPhotos: [],
    isLoggedIn: false,
    showNoticeModal: false,
    selectedNotice: null
  },

  onLoad() {
    this.checkLogin()
    this.loadHomepage()
  },

  onShow() {
    this.checkLogin()
    this.loadHomepage()
  },

  checkLogin() {
    const app = getApp()
    this.setData({ isLoggedIn: app.globalData.userType === 'parent' && !!app.globalData.token })
  },

  loadHomepage() {
    api.request({ url: '/public/homepage' })
      .then((data) => {
        this.setData({
          schoolName: data.school_name || '智慧托班',
          welcomeMessage: data.welcome_message || '用心陪伴每一个孩子',
          contactWechat: data.contact_wechat || '',
          contactPhone: data.contact_phone || '',
          notices: (data.notices || []).map(n => ({
            id: n.id,
            title: n.title,
            content: n.content || '',
            notice_type: n.notice_type || ''
          })),
          latestNotice: (data.notices && data.notices.length > 0) ? {
            id: data.notices[0].id,
            title: data.notices[0].title,
            content: data.notices[0].content || '',
            notice_type: data.notices[0].notice_type || ''
          } : null,
          feeStandard: (data.fee_standard || []).filter(f => {
            const amount = parseFloat(f.amount)
            return !isNaN(amount) && amount > 0
          }).map(f => ({
            name: f.name,
            amount: f.amount,
            unit: f.unit,
            description: f.description || ''
          })),
          featuredPhotos: (data.featured_photos || []).map(p => ({
            id: p.id,
            url: api.imageUrl(p.file_path)
          }))
        })
      })
      .catch(() => {})
  },

  goTeacherLogin() {
    wx.navigateTo({ url: '/pages/teacher/login/login' })
  },

  goParentLogin() {
    wx.navigateTo({ url: '/pages/parent/login/login' })
  },

  previewPhoto(e) {
    const url = e.currentTarget.dataset.url
    wx.previewImage({ urls: [url] })
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
    const wechat = this.data.contactWechat
    if (wechat) {
      wx.setClipboardData({
        data: wechat,
        success: () => {
          wx.showToast({ title: '微信号已复制', icon: 'success' })
        }
      })
    }
  },

  callPhone() {
    const phone = this.data.contactPhone
    if (phone) {
      wx.makePhoneCall({ phoneNumber: phone })
    }
  }
})
