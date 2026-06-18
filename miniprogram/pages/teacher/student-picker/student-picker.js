// 学生选择页（拍照后选择学生）
const api = require('../../../utils/api')
const util = require('../../../utils/util')

const PHOTO_TYPE_META = {
  activity: {
    requiresStudent: false,
    studentLabel: '关联学生（可选）',
    typeHint: '家长会、讲座等公共活动可直接保存',
    confirmText: '保存为活动照片',
    emptyMessage: ''
  },
  homework: {
    requiresStudent: true,
    studentLabel: '关联学生（必选）',
    typeHint: '作业照片需要关联学生',
    confirmText: '确认保存',
    emptyMessage: '作业照片需要先选择学生'
  },
  meal: {
    requiresStudent: false,
    studentLabel: '关联学生（可选）',
    typeHint: '餐食照片可直接保存，也可关联孩子',
    confirmText: '保存为餐食照片',
    emptyMessage: ''
  },
  daily: {
    requiresStudent: false,
    studentLabel: '关联学生（可选）',
    typeHint: '不选学生时保存到日常照片库',
    confirmText: '保存为日常照片',
    emptyMessage: ''
  }
}

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
    saving: false,
    requiresStudent: false,
    studentLabel: PHOTO_TYPE_META.activity.studentLabel,
    typeHint: PHOTO_TYPE_META.activity.typeHint,
    confirmText: PHOTO_TYPE_META.activity.confirmText,
    confirmBlocked: false,
    emptyStudentMessage: ''
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
    }, () => this.updateArchiveMeta())
    this.loadStudents()
  },

  loadStudents() {
    util.showLoading('加载学生...')
    api.request({ url: '/students', data: { status: '在读' } })
      .then((data) => {
        const list = (data.students || data || []).map((item) => ({
          ...item,
          id: Number(item.id),
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
    this.setData({ mode, selectedIds }, () => {
      this.refreshSelectedState()
      this.updateArchiveMeta()
    })
  },

  toggleStudent(e) {
    const id = Number(e.currentTarget.dataset.id)
    if (!id) return
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
    this.setData({ selectedIds: selected }, () => {
      this.refreshSelectedState()
      this.updateArchiveMeta()
    })
  },

  setType(e) {
    this.setData({ photoType: e.currentTarget.dataset.type }, () => this.updateArchiveMeta())
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

  updateArchiveMeta() {
    const meta = PHOTO_TYPE_META[this.data.photoType] || PHOTO_TYPE_META.daily
    const confirmBlocked = meta.requiresStudent && this.data.selectedIds.length === 0
    this.setData({
      requiresStudent: meta.requiresStudent,
      studentLabel: meta.studentLabel,
      typeHint: meta.typeHint,
      confirmText: meta.confirmText,
      confirmBlocked,
      emptyStudentMessage: meta.emptyMessage
    })
  },

  confirmAssociate() {
    if (this.data.confirmBlocked) {
      util.showError(this.data.emptyStudentMessage || '请先选择照片中的学生')
      return
    }
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
