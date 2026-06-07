// 餐食总览页
const api = require('../../../utils/api')
const util = require('../../../utils/util')

const MEAL_TYPES = ['早餐', '午餐', '晚餐', '上午加餐', '下午加餐']
const PHOTO_GROUPS = [
  { key: 'shopping', label: '🛒 采购' },
  { key: 'cooking', label: '👨‍🍳 制作' },
  { key: 'done', label: '🍽️ 成品' },
  { key: 'kids_eating', label: '👶 孩子吃饭' }
]

Page({
  data: {
    records: [],
    filteredRecords: [],
    loading: false,
    activeFilter: 'all',
    filters: [],
    mealTypes: MEAL_TYPES,

    // 状态卡
    todayCount: 0,
    todayTotal: 0,
    weekCount: 0,
    pendingTypes: [],

    // 记录弹窗
    showForm: false,
    form: {
      meal_date: '',
      meal_type: '午餐',
      menu_text: '',
      ingredient_notes: '',
      cooking_notes: '',
      hygiene_notes: '',
      overall_remark: '',
      photo_ids: { shopping: [], cooking: [], done: [], kids_eating: [] }
    },
    tempFiles: { shopping: [], cooking: [], done: [], kids_eating: [] },
    formPhotoGroups: [],
    submitting: false,

    // 空状态
    emptyTitle: '暂无餐食记录',
    emptyDesc: '记录餐食后，会出现在这里'
  },

  onLoad() {
    this.setData({ formPhotoGroups: this._buildFormPhotoGroups(this.data.tempFiles) })
    this.loadRecords()
  },

  onShow() {
    this.loadRecords()
  },

  loadRecords() {
    this.setData({ loading: true })
    api.request({ url: '/meals' })
      .then((data) => {
        const rawRecords = data.records || []
        const records = rawRecords.map(this._buildMealRow)
        this._setOverview(records)
      })
      .catch(() => {
        util.showError('加载失败')
        this.setData({ records: [], filteredRecords: [] })
      })
      .finally(() => this.setData({ loading: false }))
  },

  _buildMealRow(item) {
    const photos = item.photos || {}
    const donePhotos = (photos.done || []).map((photo) => {
      const filePath = photo.file_path || photo
      return { file_path: filePath, url: api.imageUrl(filePath) }
    })
    // 统计各分组照片数
    const photoGroupCounts = PHOTO_GROUPS.map(group => ({
      group: group.key,
      label: group.label,
      count: (photos[group.key] || []).length,
      displayText: group.label + ' ' + (photos[group.key] || []).length + '张'
    }))
    const hasPhotos = photoGroupCounts.some(g => g.count > 0)

    return {
      ...item,
      date: item.date || item.meal_date || '',
      menuText: item.menu_text || item.menu || '—',
      overallRemark: item.overall_remark || '',
      donePhotos,
      hasPhotos,
      hasDetailNotes: !!(item.ingredient_notes || item.cooking_notes || item.hygiene_notes),
      photoGroupCounts,
      showDetail: false
    }
  },

  _setOverview(records) {
    const today = util.today()

    // 今日记录
    const todayRecords = records.filter(r => r.date === today)
    const todayRecordedTypes = todayRecords.map(r => r.meal_type)
    const pendingTypes = MEAL_TYPES.filter(t => !todayRecordedTypes.includes(t))
    const todayCount = todayRecords.length

    // 本周记录（近7天）
    const weekAgo = util.dateOffset(-6)
    const weekRecords = records.filter(r => r.date >= weekAgo)
    const weekCount = weekRecords.length

    // 生成筛选
    const filters = [
      { key: 'all', label: '全部', count: records.length },
      { key: 'today', label: '今日', count: todayCount },
      { key: 'week', label: '本周', count: weekCount }
    ].map(item => ({ ...item, className: item.key === this.data.activeFilter ? 'active' : '' }))

    this.setData({
      records,
      todayCount,
      todayTotal: todayCount,
      weekCount,
      pendingTypes,
      filters
    })
    this._applyFilter()
  },

  _applyFilter() {
    const filter = this.data.activeFilter
    const today = util.today()
    const weekAgo = util.dateOffset(-6)
    let list = this.data.records

    if (filter === 'today') list = list.filter(r => r.date === today)
    if (filter === 'week') list = list.filter(r => r.date >= weekAgo)

    const emptyMap = {
      all: ['暂无餐食记录', '记录餐食后，会出现在这里'],
      today: ['今日暂无餐食记录', '记录今日餐食后显示在此'],
      week: ['本周暂无餐食记录', '记录餐食后自动汇总']
    }
    const empty = emptyMap[filter] || emptyMap.all

    this.setData({
      filteredRecords: list,
      emptyTitle: empty[0],
      emptyDesc: empty[1]
    })
  },

  switchFilter(e) {
    const filter = e.currentTarget.dataset.filter
    if (filter === this.data.activeFilter) return
    this.setData({
      activeFilter: filter,
      filters: this.data.filters.map(item => ({ ...item, className: item.key === filter ? 'active' : '' }))
    })
    this._applyFilter()
  },

  toggleDetail(e) {
    const index = e.currentTarget.dataset.index
    const key = 'filteredRecords[' + index + '].showDetail'
    this.setData({ [key]: !this.data.filteredRecords[index].showDetail })
  },

  // 记录今日餐食
  openForm() {
    const today = util.today()
    this.setData({
      showForm: true,
      form: {
        meal_date: today,
        meal_type: '午餐',
        menu_text: '',
        ingredient_notes: '',
        cooking_notes: '',
        hygiene_notes: '',
        overall_remark: '',
        photo_ids: { shopping: [], cooking: [], done: [], kids_eating: [] }
      },
      tempFiles: { shopping: [], cooking: [], done: [], kids_eating: [] }
    })
    this._refreshFormPhotoGroups()
  },

  openFormForType(e) {
    const mealType = e.currentTarget.dataset.type
    const today = util.today()
    this.setData({
      showForm: true,
      form: {
        meal_date: today,
        meal_type: mealType,
        menu_text: '',
        ingredient_notes: '',
        cooking_notes: '',
        hygiene_notes: '',
        overall_remark: '',
        photo_ids: { shopping: [], cooking: [], done: [], kids_eating: [] }
      },
      tempFiles: { shopping: [], cooking: [], done: [], kids_eating: [] }
    })
    this._refreshFormPhotoGroups()
  },

  closeForm() {
    this.setData({ showForm: false })
  },

  _buildFormPhotoGroups(tempFiles) {
    return PHOTO_GROUPS.map(group => ({
      key: group.key,
      label: group.label,
      files: (tempFiles[group.key] || []).map(path => ({ path }))
    }))
  },

  _refreshFormPhotoGroups() {
    this.setData({ formPhotoGroups: this._buildFormPhotoGroups(this.data.tempFiles) })
  },

  onFormField(e) {
    const field = e.currentTarget.dataset.field
    this.setData({ ['form.' + field]: e.detail.value })
  },

  onMealTypeChange(e) {
    const idx = parseInt(e.detail.value)
    this.setData({ 'form.meal_type': MEAL_TYPES[idx] })
  },

  addGroupPhotos(e) {
    const group = e.currentTarget.dataset.group
    const remain = 9 - (this.data.tempFiles[group]?.length || 0)
    if (remain <= 0) return

    wx.chooseMedia({
      count: remain,
      mediaType: ['image'],
      sourceType: ['camera', 'album'],
      success: (res) => {
        const files = res.tempFiles.map(f => f.tempFilePath)
        const key = 'tempFiles.' + group
        this.setData({ [key]: [...(this.data.tempFiles[group] || []), ...files] })
        this._refreshFormPhotoGroups()
        this._uploadGroupPhotos(group, files)
      }
    })
  },

  _uploadGroupPhotos(group, files) {
    util.showLoading('上传照片...')
    Promise.all(files.map(f => api.uploadFile(f)))
      .then((results) => {
        const ids = results.map(r => r.photo_id)
        const key = 'form.photo_ids.' + group
        this.setData({ [key]: [...(this.data.form.photo_ids[group] || []), ...ids] })
      })
      .catch(() => util.showError('部分照片上传失败'))
      .finally(() => wx.hideLoading())
  },

  removeGroupPhoto(e) {
    const group = e.currentTarget.dataset.group
    const idx = parseInt(e.currentTarget.dataset.index)
    const files = [...(this.data.tempFiles[group] || [])]
    const ids = [...(this.data.form.photo_ids[group] || [])]
    files.splice(idx, 1)
    ids.splice(idx, 1)
    this.setData({
      ['tempFiles.' + group]: files,
      ['form.photo_ids.' + group]: ids
    })
    this._refreshFormPhotoGroups()
  },

  submitMeal() {
    if (!this.data.form.menu_text.trim()) {
      util.showError('请填写菜单')
      return
    }
    this.setData({ submitting: true })
    api.request({
      url: '/meals',
      method: 'POST',
      data: this.data.form
    }).then(() => {
      util.showSuccess('保存成功')
      this.setData({ showForm: false })
      this.loadRecords()
    }).catch((err) => {
      util.showError(err.message || '保存失败')
    }).finally(() => this.setData({ submitting: false }))
  }
})
