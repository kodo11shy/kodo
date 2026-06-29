// 餐食记录：每天一条今日餐食
const api = require('../../../utils/api')
const util = require('../../../utils/util')

Page({
  data: {
    loading: false,
    records: [],
    todayMeal: null,
    todayRecorded: false,
    todayStatusText: '未记录',
    primaryActionText: '记录今日餐食',
    weekRecordedDays: 0,
    monthRecordedDays: 0,
    emptyTitle: '暂无餐食记录',
    emptyDesc: '记录今日餐食后，会出现在这里',

    showForm: false,
    editingMealId: null,
    submitting: false,
    formTitle: '记录今日餐食',
    form: {
      meal_date: '',
      menu_text: '',
      overall_remark: ''
    },
    tempFiles: [],
    selectedPhotoIds: [],
    coverPhotoId: null,
    selectedStudentIds: [],
    studentRows: [],
    photoRows: [],
    photoLibraryLoading: false
  },

  onLoad() {
    this.loadPage()
  },

  onShow() {
    this.loadPage()
  },

  loadPage() {
    this.setData({ loading: true })
    Promise.all([
      api.request({ url: '/meals/today' }),
      api.request({ url: '/meals', data: { page: 1, page_size: 30 } })
    ])
      .then(([todayData, listData]) => {
        const todayMeal = todayData.meal ? this._buildMealRow(todayData.meal) : null
        const records = (listData.records || []).map(item => this._buildMealRow(item))
        this.setData({
          todayMeal,
          records,
          todayRecorded: !!todayData.recorded,
          todayStatusText: todayData.recorded ? '已记录' : '未记录',
          primaryActionText: todayData.recorded ? '编辑今日餐食' : '记录今日餐食',
          weekRecordedDays: todayData.week_recorded_days || 0,
          monthRecordedDays: todayData.month_recorded_days || 0,
          _todayDefaults: {
            date: todayData.date || util.today(),
            defaultStudents: todayData.default_students || [],
            allStudents: todayData.all_students || []
          }
        })
      })
      .catch((err) => {
        util.showError(err.message || '加载餐食失败')
      })
      .finally(() => this.setData({ loading: false }))
  },

  _buildMealRow(item) {
    const photos = (item.photos || []).map(photo => ({
      ...photo,
      url: api.imageUrl(photo.thumbnail || photo.file_path),
      previewUrl: api.imageUrl(photo.file_path || photo.thumbnail)
    })).filter(photo => photo.url)
    const cover = item.cover_photo || photos[0] || null
    return {
      ...item,
      date: item.date || item.meal_date || '',
      menuText: item.menu_text || item.menu || '未填写菜单',
      remarkText: item.overall_remark || '',
      photos,
      coverUrl: cover ? api.imageUrl(cover.thumbnail || cover.file_path || cover.url) : '',
      coverPreviewUrl: cover ? api.imageUrl(cover.file_path || cover.thumbnail || cover.previewUrl || cover.url) : '',
      photoCount: item.photo_count != null ? item.photo_count : photos.length,
      studentCount: item.student_count != null ? item.student_count : (item.students || []).length,
      studentNames: (item.students || []).map(student => student.name).join('、'),
      photoIds: item.photo_ids || photos.map(photo => photo.id),
      studentIds: item.student_ids || (item.students || []).map(student => student.id),
      coverPhotoId: item.cover_photo_id || (cover ? cover.id : null)
    }
  },

  openTodayForm() {
    if (this.data.todayMeal) {
      this.openEditForm({ currentTarget: { dataset: { id: this.data.todayMeal.id } } })
      return
    }
    this._openFormWithMeal(null)
  },

  openEditForm(e) {
    const mealId = Number(e.currentTarget.dataset.id)
    const existing = this.data.records.find(item => item.id === mealId) || this.data.todayMeal
    if (!mealId || !existing) return

    api.request({ url: '/meals/' + mealId })
      .then((data) => {
        this._openFormWithMeal(this._buildMealRow(data.meal || existing))
      })
      .catch(() => {
        this._openFormWithMeal(existing)
      })
  },

  _openFormWithMeal(meal) {
    const defaults = this.data._todayDefaults || {}
    const defaultStudents = meal ? [] : (defaults.defaultStudents || [])
    const selectedStudentIds = meal ? (meal.studentIds || []) : defaultStudents.map(item => item.id)
    const selectedPhotoIds = meal ? (meal.photoIds || []) : []
    const coverPhotoId = meal ? meal.coverPhotoId : null

    this.setData({
      showForm: true,
      editingMealId: meal ? meal.id : null,
      formTitle: meal ? '编辑今日餐食' : '记录今日餐食',
      form: {
        meal_date: meal ? meal.date : (defaults.date || util.today()),
        menu_text: meal ? meal.menuText : '',
        overall_remark: meal ? meal.remarkText : ''
      },
      tempFiles: [],
      selectedPhotoIds,
      coverPhotoId,
      selectedStudentIds
    })
    this.loadFormOptions()
  },

  closeForm() {
    if (this.data.submitting) return
    this.setData({ showForm: false })
  },

  loadFormOptions() {
    this.setData({ photoLibraryLoading: true })
    Promise.all([
      api.request({ url: '/students', data: { status: '在读' } }).catch(() => ({ students: [] })),
      api.request({ url: '/photos', data: { page: 1, page_size: 60 } }).catch(() => ({ photos: [] }))
    ])
      .then(([studentsData, photosData]) => {
        const fallbackStudents = (this.data._todayDefaults && this.data._todayDefaults.allStudents) || []
        const students = (studentsData.students && studentsData.students.length > 0)
          ? studentsData.students
          : fallbackStudents
        const studentRows = students.map(student => ({
          id: student.id,
          name: student.name,
          grade: student.grade || '',
          selected: this.data.selectedStudentIds.includes(student.id)
        }))
        const photoRows = (photosData.photos || []).map(photo => ({
          id: photo.id,
          url: api.imageUrl(photo.thumbnail || photo.file_path),
          previewUrl: api.imageUrl(photo.file_path || photo.thumbnail),
          remark: photo.remark || '',
          selected: this.data.selectedPhotoIds.includes(photo.id),
          isCover: this.data.coverPhotoId === photo.id
        })).filter(photo => photo.url)
        this.setData({ studentRows, photoRows })
      })
      .finally(() => this.setData({ photoLibraryLoading: false }))
  },

  onFormField(e) {
    const field = e.currentTarget.dataset.field
    this.setData({ ['form.' + field]: e.detail.value })
  },

  onDateChange(e) {
    this.setData({ 'form.meal_date': e.detail.value })
  },

  toggleStudent(e) {
    const id = Number(e.currentTarget.dataset.id)
    const selected = new Set(this.data.selectedStudentIds)
    if (selected.has(id)) selected.delete(id)
    else selected.add(id)
    const ids = Array.from(selected)
    this.setData({
      selectedStudentIds: ids,
      studentRows: this.data.studentRows.map(item => ({ ...item, selected: ids.includes(item.id) }))
    })
  },

  toggleLibraryPhoto(e) {
    const id = Number(e.currentTarget.dataset.id)
    const selected = new Set(this.data.selectedPhotoIds)
    if (selected.has(id)) selected.delete(id)
    else selected.add(id)
    const ids = Array.from(selected)
    const coverPhotoId = ids.includes(this.data.coverPhotoId) ? this.data.coverPhotoId : (ids[0] || null)
    this.setData({
      selectedPhotoIds: ids,
      coverPhotoId,
      photoRows: this.data.photoRows.map(item => ({
        ...item,
        selected: ids.includes(item.id),
        isCover: coverPhotoId === item.id
      }))
    })
  },

  setCoverPhoto(e) {
    const id = Number(e.currentTarget.dataset.id)
    if (!this.data.selectedPhotoIds.includes(id)) return
    this.setData({
      coverPhotoId: id,
      photoRows: this.data.photoRows.map(item => ({ ...item, isCover: item.id === id }))
    })
  },

  addPhotos() {
    const remain = 9 - this.data.tempFiles.length
    if (remain <= 0) {
      util.showError('最多添加 9 张新照片')
      return
    }
    wx.chooseMedia({
      count: remain,
      mediaType: ['image'],
      sourceType: ['camera', 'album'],
      success: (res) => {
        const files = res.tempFiles.map(file => ({ path: file.tempFilePath }))
        this.setData({ tempFiles: [...this.data.tempFiles, ...files] })
      }
    })
  },

  removeTempPhoto(e) {
    const index = Number(e.currentTarget.dataset.index)
    const files = [...this.data.tempFiles]
    files.splice(index, 1)
    this.setData({ tempFiles: files })
  },

  _uploadNewPhotos() {
    const uploadedIds = []
    let chain = Promise.resolve()
    this.data.tempFiles.forEach((file) => {
      chain = chain
        .then(() => api.uploadFile(file.path))
        .then((result) => {
          if (result && result.photo_id) uploadedIds.push(result.photo_id)
        })
    })
    return chain.then(() => uploadedIds)
  },

  _rollbackUploadedPhotos(uploadedIds) {
    if (!uploadedIds || uploadedIds.length === 0) return Promise.resolve()
    return api.request({
      url: '/photos/batch',
      method: 'POST',
      data: { operation: 'delete', photo_ids: uploadedIds }
    }).catch(() => null)
  },

  submitMeal() {
    const menu = (this.data.form.menu_text || '').trim()
    if (!menu) {
      util.showError('请填写今天吃了什么')
      return
    }
    if (this.data.selectedStudentIds.length === 0) {
      util.showError('请选择关联学生')
      return
    }

    this.setData({ submitting: true })
    util.showLoading('保存中...')
    let uploadedIds = []
    this._uploadNewPhotos()
      .then((ids) => {
        uploadedIds = ids
        const photoIds = [...this.data.selectedPhotoIds, ...uploadedIds]
        const coverPhotoId = this.data.coverPhotoId || photoIds[0] || null
        const payload = {
          meal_date: this.data.form.meal_date,
          menu_text: menu,
          overall_remark: this.data.form.overall_remark || '',
          photo_ids: photoIds,
          cover_photo_id: coverPhotoId,
          student_ids: this.data.selectedStudentIds
        }
        const mealId = this.data.editingMealId
        return api.request({
          url: mealId ? '/meals/' + mealId : '/meals',
          method: mealId ? 'PUT' : 'POST',
          data: payload
        })
      })
      .then(() => {
        uploadedIds = []
        wx.hideLoading()
        util.showSuccess('保存成功')
        this.setData({ showForm: false })
        this.loadPage()
      })
      .catch((err) => {
        wx.hideLoading()
        this._rollbackUploadedPhotos(uploadedIds)
        util.showError(err.message || '保存失败')
      })
      .finally(() => {
        this.setData({ submitting: false })
      })
  },

  previewMealPhoto(e) {
    const url = e.currentTarget.dataset.url
    if (!url) return
    wx.previewImage({ urls: [url] })
  }
})
