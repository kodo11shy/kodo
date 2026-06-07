// 拍照页（支持单张拍摄+批量本地上传）
const api = require('../../../utils/api')
const util = require('../../../utils/util')

Page({
  data: {
    // 单张模式
    photoPath: '',
    uploading: false,
    uploadProgress: 0,

    // 批量模式
    batchMode: false,
    selectedPhotos: [],
    batchUploading: false,
    batchProgress: 0,
    batchStatusText: '',
    uploadResults: []
  },

  // ======== 单张拍照（保持原有逻辑） ========

  takePhoto() {
    wx.chooseMedia({
      count: 1,
      mediaType: ['image'],
      sourceType: ['camera'],
      camera: 'back',
      success: (res) => {
        this.setData({ photoPath: res.tempFiles[0].tempFilePath, batchMode: false })
      },
      fail: (err) => {
        if (err.errMsg.indexOf('cancel') === -1) {
          util.showError('拍照失败')
        }
      }
    })
  },

  // 从相册选一张（保持原有逻辑）
  chooseFromAlbum() {
    wx.chooseMedia({
      count: 1,
      mediaType: ['image'],
      sourceType: ['album'],
      success: (res) => {
        this.setData({ photoPath: res.tempFiles[0].tempFilePath, batchMode: false })
      },
      fail: (err) => {
        if (err.errMsg.indexOf('cancel') === -1) {
          util.showError('选择失败')
        }
      }
    })
  },

  retake() {
    this.setData({ photoPath: '', uploadProgress: 0 })
  },

  uploadPhoto() {
    if (!this.data.photoPath || this.data.uploading) return
    this.setData({ uploading: true, uploadProgress: 10 })

    api.uploadFile(this.data.photoPath)
      .then((data) => {
        this.setData({ uploadProgress: 100 })
        wx.navigateTo({
          url: '/pages/teacher/student-picker/student-picker?photo_id=' + data.photo_id + '&file_path=' + encodeURIComponent(data.file_path)
        })
      })
      .catch((err) => {
        util.showError(err.message || '上传失败')
        this.setData({ uploading: false, uploadProgress: 0 })
      })
  },

  // ======== 批量本地上传（新增） ========

  // 从相册选多张 — 批量上传到照片库
  batchUpload() {
    wx.chooseMedia({
      count: 9,
      mediaType: ['image'],
      sourceType: ['album'],
      success: (res) => {
        const photos = res.tempFiles.map((f, i) => ({
          id: 'photo_' + i + '_' + Date.now(),
          path: f.tempFilePath,
          size: f.size || 0,
          uploaded: false,
          photoId: null
        }))
        this.setData({
          batchMode: true,
          selectedPhotos: photos,
          uploadResults: [],
          batchProgress: 0,
          batchStatusText: ''
        })
      },
      fail: (err) => {
        if (err.errMsg.indexOf('cancel') === -1) {
          util.showError('选择失败')
        }
      }
    })
  },

  // 移除已选中的某张
  removeSelected(e) {
    const index = e.currentTarget.dataset.index
    const photos = [...this.data.selectedPhotos]
    photos.splice(index, 1)
    this.setData({ selectedPhotos: photos })
    if (photos.length === 0) {
      this.setData({ batchMode: false })
    }
  },

  // 执行批量上传
  doBatchUpload() {
    const photos = this.data.selectedPhotos.filter(p => !p.uploaded)
    if (photos.length === 0) {
      util.showError('没有待上传的照片')
      return
    }

    this.setData({ batchUploading: true, batchProgress: 0 })
    const results = []
    const total = photos.length
    let completed = 0

    // 逐个上传
    const uploadNext = (index) => {
      if (index >= total) {
        // 全部完成
        this.setData({
          batchUploading: false,
          batchProgress: 100,
          batchStatusText: '全部上传完成！',
          uploadResults: results
        })
        wx.showToast({ title: '上传完成 ' + total + ' 张', icon: 'success' })

        // 跳转到照片库
        setTimeout(() => {
          wx.redirectTo({ url: '/pages/teacher/photolib/photolib' })
        }, 1200)
        return
      }

      const photo = photos[index]
      this.setData({
        batchStatusText: '正在上传 ' + (index + 1) + '/' + total + '...',
        batchProgress: Math.round((index / total) * 90)
      })

      api.uploadFile(photo.path)
        .then((data) => {
          results.push({ path: photo.path, photoId: data.photo_id, filePath: data.file_path })
          completed++
          // 更新选中列表状态
          const updatedPhotos = [...this.data.selectedPhotos]
          const idx = updatedPhotos.findIndex(p => p.id === photo.id)
          if (idx > -1) {
            updatedPhotos[idx].uploaded = true
            updatedPhotos[idx].photoId = data.photo_id
          }
          this.setData({
            selectedPhotos: updatedPhotos,
            batchProgress: Math.round((completed / total) * 100)
          })
          uploadNext(index + 1)
        })
        .catch((err) => {
          util.showError('第' + (index + 1) + '张上传失败：' + (err.message || '未知错误'))
          uploadNext(index + 1)
        })
    }

    uploadNext(0)
  },

  // 取消批量，回到单张模式
  cancelBatch() {
    this.setData({
      batchMode: false,
      selectedPhotos: [],
      batchUploading: false,
      batchProgress: 0,
      batchStatusText: '',
      uploadResults: []
    })
  }
})
