// 学生选择页（拍照后选择学生）
const api = require('../../../utils/api')
const util = require('../../../utils/util')

Page({
  data: {
    photoId: 0,
    batchPhotoIds: [],
    isBatch: false,
    photoPath: '',
    mode: 'multi',
    students: [],
    selectedIds: [],
    photoUrl: '',
    photoType: 'activity',
    remark: '',
    saving: false
  },

  onLoad(options) {
    const photoId = parseInt(options.photo_id || 0)
    const photoPath = decodeURIComponent(options.file_path || '')
    const batchPhotoIds = options.batch_photo_ids
      ? options.batch_photo_ids.split(',').map(id => parseInt(id)).filter(id => id > 0)
      : []
    this.setData({
      photoId,
      photoPath,
      photoUrl: api.imageUrl(photoPath),
      batchPhotoIds,
      isBatch: batchPhotoIds.length > 0
    })
    this.loadStudents()
  },

  loadStudents() {
    util.showLoading('加载学生...')
    api.request({ url: '/students', data: { status: '在读' } })
      .then((data) => {
        const list = (data.students || data || []).map((item) => ({
          ...item,
          initial: (item.name || '').slice(0, 1),
          selected: false
        }))
        this.setData({ students: list })
      })
      .catch(() => {
        util.showError('加载学生失败')
      })
      .finally(() => {
        wx.hideLoading()
      })
  },

  switchMode(e) {
    const mode = e.currentTarget.dataset.mode
    const selectedIds = mode === 'single' && this.data.selectedIds.length > 1 ? [this.data.selectedIds[0]] : this.data.selectedIds
    this.setData({ mode, selectedIds }, () => this.refreshSelectedState())
  },

  toggleStudent(e) {
    const id = e.currentTarget.dataset.id
    let selected = [...this.data.selectedIds]

    if (this.data.mode === 'single') {
      selected = selected.includes(id) ? [] : [id]
    } else {
      const idx = selected.indexOf(id)
      if (idx > -1) {
        selected.splice(idx, 1)
      } else {
        selected.push(id)
      }
    }
    this.setData({ selectedIds: selected }, () => this.refreshSelectedState())
  },

  setType(e) {
    this.setData({ photoType: e.currentTarget.dataset.type })
  },

  onRemarkInput(e) {
    this.setData({ remark: e.detail.value })
  },

  refreshSelectedState() {
    const selectedSet = new Set(this.data.selectedIds)
    const students = this.data.students.map((item) => ({
      ...item,
      selected: selectedSet.has(item.id)
    }))
    this.setData({ students })
  },

  confirmAssociate() {
    if (this.data.selectedIds.length === 0) return
    this.setData({ saving: true })

    const payload = {
      student_ids: this.data.selectedIds,
      photo_type: this.data.photoType,
      remark: this.data.remark
    }

    // 批量照片关联（来自照片库）
    if (this.data.batchPhotoIds && this.data.batchPhotoIds.length > 0) {
      api.request({
        url: '/photos/batch/associate',
        method: 'POST',
        data: {
          ...payload,
          photo_ids: this.data.batchPhotoIds
        }
      }).then(() => {
        util.showSuccess('关联成功')
        setTimeout(() => {
          wx.navigateBack({ delta: 1 })
        }, 500)
      }).catch((err) => {
        util.showError(err.message || '保存失败')
      }).finally(() => {
        this.setData({ saving: false })
      })
      return
    }

    // 单张照片关联（标准流程）
    api.request({
      url: '/photos/' + this.data.photoId + '/associate',
      method: 'POST',
      data: payload
    }).then(() => {
      util.showSuccess('保存成功')

      // 根据照片类型跳转
      if (this.data.photoType === 'homework') {
        wx.redirectTo({
          url: '/pages/teacher/homework/create/homework-create?photo_id=' + this.data.photoId + '&student_ids=' + this.data.selectedIds.join(',')
        })
      } else {
        setTimeout(() => {
          wx.navigateBack({ delta: 2 })
        }, 500)
      }
    }).catch((err) => {
      util.showError(err.message || '保存失败')
    }).finally(() => {
      this.setData({ saving: false })
    })
  }
})
