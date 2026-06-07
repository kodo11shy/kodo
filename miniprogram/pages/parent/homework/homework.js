// 家长端作业查看（只读）
const api = require('../../../utils/api')
const util = require('../../../utils/util')

const FIXED_HOMEWORK_SUBJECTS = ['语文', '数学']

Page({
  data: {
    studentId: 0,
    studentName: '',
    records: [],
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
    api.request({ url: '/parent/homework/' + this.data.studentId })
      .then((data) => {
        const records = (data.records || [])
          .filter(item => FIXED_HOMEWORK_SUBJECTS.includes(item.subject))
          .map((item) => {
          const photos = item.photos || {}
          return {
            ...item,
            homeworkTypeText: item.homework_type || '作业',
            statusClass: this.getStatusClass(item.status),
            statusIcon: this.getStatusText(item.status),
            photos: {
              done: this.normalizePhotos(photos.done),
              graded: this.normalizePhotos(photos.graded),
              corrected: this.normalizePhotos(photos.corrected)
            }
          }
        })
        this.setData({ records })
      })
      .catch(() => util.showError('加载失败'))
      .finally(() => this.setData({ loading: false }))
  },

  getStatusClass(status) {
    const map = { '待批改': 'pending', '已批改': 'graded', '已完成': 'done' }
    return map[status] || 'pending'
  },

  getStatusText(status) {
    const map = { '待批改': '⏳', '已批改': '✅', '已完成': '🎉' }
    return map[status] || status
  },

  normalizePhotos(list) {
    return (list || []).map((item) => {
      const filePath = item.file_path || item
      return {
        file_path: filePath,
        url: api.imageUrl(filePath)
      }
    })
  },

  previewPhotos(e) {
    const list = e.currentTarget.dataset.list || []
    const urls = list.map(item => item.url || api.imageUrl(item.file_path || item))
    if (urls.length > 0) {
      wx.previewImage({ urls, current: urls[0] })
    }
  },

  // 长按保存作业照片
  saveHomeworkPhoto(e) {
    const url = e.currentTarget.dataset.src
    if (!url) return
    wx.showLoading({ title: '保存中...' })
    wx.downloadFile({
      url: url,
      success: (res) => {
        wx.saveImageToPhotosAlbum({
          filePath: res.tempFilePath,
          success: () => util.showSuccess('已保存到相册'),
          fail: () => util.showError('保存失败，请检查相册权限')
        })
      },
      fail: () => util.showError('下载失败'),
      complete: () => wx.hideLoading()
    })
  },
  // 图片 URL 在 loadData 中预处理，避免 WXML 调用函数。
})
