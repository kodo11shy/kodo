// 照片库总览（中转站）
const api = require('../../../utils/api')
const util = require('../../../utils/util')

Page({
  data: {
    loading: false,
    photos: [],
    page: 1,
    pageSize: 30,
    hasMore: true,
    refreshing: false,

    // 总览卡
    totalCount: 0,
    featuredCount: 0,
    unassociatedCount: 0,

    // 待处理
    unassociatedPhotos: [],

    // 筛选
    filterTab: 'all',
    filterTabs: [
      { key: 'all', label: '全部', className: 'active' },
      { key: 'unassociated', label: '未分类', className: '' },
      { key: 'featured', label: '精选', className: '' }
    ],

    // 长按菜单
    showMenu: false,
    menuPhoto: null,
    menuIndex: 0,

    // 多选模式
    multiMode: false,
    selectedIds: [],
    selectedPhotos: [],

    // 操作确认弹窗
    showConfirm: false,
    confirmTitle: '',
    confirmText: '',
    confirmAction: null,

    // 标签选择器
    showTagPicker: false,
    tagPickerPhoto: null,
    tagOptions: [
      { key: 'general', label: '日常' },
      { key: 'activity', label: '活动' },
      { key: 'homework', label: '作业' },
      { key: 'meal', label: '餐食' },
      { key: 'daily', label: '生活' },
    ],
  },

  onLoad() {
    this.loadPhotos()
  },

  onShow() {
    if (this.data.photos.length > 0) {
      this.loadPhotos(true)
    }
  },

  onPullDownRefresh() {
    this.loadPhotos(true).finally(() => wx.stopPullDownRefresh())
  },

  onReachBottom() {
    if (this.data.hasMore && !this.data.loading) {
      this.loadMore()
    }
  },

  // ======== 数据加载 ========

  loadPhotos(refresh) {
    return new Promise((resolve) => {
      if (refresh) {
        this.setData({ page: 1, hasMore: true, refreshing: true })
      }
      this.setData({ loading: true })

      const loadTask = this._loadPhotoList(refresh)

      if (refresh) {
        // 首次/刷新时同时加载统计数据
        Promise.all([
          loadTask,
          api.request({ url: '/photos', data: { page: 1, page_size: 1 } }).catch(() => null),
          api.request({ url: '/photos', data: { associated: false, page: 1, page_size: 1 } }).catch(() => null),
          api.request({ url: '/photos/featured', data: { page: 1, page_size: 1 } }).catch(() => null)
        ]).then(([photoList, allData, unassociatedData, featuredData]) => {
          const totalCount = allData?.total || (photoList || []).length
          const unassociatedCount = unassociatedData?.total || 0
          const featuredCount = featuredData?.total || 0

          let unassociatedPhotos = []
          if (unassociatedCount > 0) {
            unassociatedPhotos = [{ text: unassociatedCount + ' 张照片未关联学生', count: unassociatedCount }]
          }

          this.setData({ totalCount, featuredCount, unassociatedCount, unassociatedPhotos })
          resolve()
        }).catch(() => resolve())
      } else {
        // 加载更多时不重新请求统计数据
        loadTask.then(resolve).catch(() => resolve())
      }
    })
  },

  _loadPhotoList(refresh) {
    return new Promise((resolve) => {
      const params = {
        page: refresh ? 1 : this.data.page,
        page_size: this.data.pageSize
      }

      if (this.data.filterTab === 'unassociated') {
        params.associated = false
      } else if (this.data.filterTab === 'featured') {
        this._loadFeaturedPhotos(refresh).then(resolve)
        return
      }

      api.request({ url: '/photos', data: params })
        .then((data) => {
          const photos = (data.photos || []).map(p => this._formatPhoto(p))
          this._handleLoaded(photos, data.total || 0, refresh)
          resolve()
        })
        .catch(() => {
          if (refresh) this.setData({ photos: [], refreshing: false })
          resolve()
        })
        .finally(() => this.setData({ loading: false, refreshing: false }))
    })
  },

  _loadFeaturedPhotos(refresh) {
    return new Promise((resolve) => {
      api.request({
        url: '/photos/featured',
        data: { page: refresh ? 1 : this.data.page, page_size: this.data.pageSize }
      }).then((data) => {
        const photos = (data.photos || []).map(p => this._formatPhoto(p))
        this._handleLoaded(photos, photos.length, refresh)
        resolve()
      }).catch(() => {
        if (refresh) this.setData({ photos: [], refreshing: false })
        resolve()
      }).finally(() => {
        this.setData({ loading: false, refreshing: false })
      })
    })
  },

  loadMore() {
    this.setData({ page: this.data.page + 1 })
    this._loadPhotoList()
  },

  _formatPhoto(p) {
    const localTags = this._getLocalTags()
    const localTag = localTags[p.id]
    return {
      id: p.id,
      url: api.imageUrl(p.file_path),
      filePath: p.file_path,
      photoType: p.photo_type,
      photoTypeLabel: localTag ? this._typeLabel(localTag) : (this._typeLabel(p.photo_type) || ''),
      localTag: localTag || '',
      isFeatured: p.is_featured || false,
      takenAt: p.taken_at ? util.formatDate(p.taken_at) : '',
      remark: p.remark || '',
      selected: false,
      checkboxClass: '',
      tagOptionClass: ''
    }
  },

  _typeLabel(type) {
    const map = { general: '日常', activity: '活动', homework: '作业', meal: '餐食', daily: '生活' }
    return map[type] || type || '日常'
  },

  _handleLoaded(newPhotos, total, refresh) {
    const existing = refresh ? [] : this.data.photos
    const merged = refresh ? newPhotos : existing.concat(newPhotos)
    this.setData({
      photos: merged,
      hasMore: newPhotos.length >= this.data.pageSize,
      refreshing: false
    })
  },

  _getLocalTags() {
    if (this._localTagsCache) return this._localTagsCache
    try {
      this._localTagsCache = wx.getStorageSync('photolib_tags') || {}
    } catch (e) {
      this._localTagsCache = {}
    }
    return this._localTagsCache
  },

  _saveLocalTags(tags) {
    try {
      wx.setStorageSync('photolib_tags', tags)
      this._localTagsCache = tags
    } catch (e) { util.showError('标签保存失败') }
  },

  // ======== 筛选切换 ========

  switchFilter(e) {
    const key = e.currentTarget.dataset.key
    if (key === this.data.filterTab) return
    this.setData({
      filterTab: key,
      filterTabs: this.data.filterTabs.map(item => ({ ...item, className: item.key === key ? 'active' : '' })),
      photos: [],
      page: 1,
      hasMore: true,
      multiMode: false,
      selectedIds: []
    })
    this.loadPhotos(true)
  },

  // ======== 照片预览 ========

  tapPhoto(e) {
    if (this.data.multiMode) {
      this.toggleSelect(e)
      return
    }
    const index = e.currentTarget.dataset.index
    const photo = this.data.photos[index]
    if (!photo) return
    const urls = this.data.photos.map(p => p.url)
    wx.previewImage({ current: photo.url, urls })
  },

  // ======== 长按菜单 ========

  onLongPress(e) {
    if (this.data.multiMode) return
    const index = e.currentTarget.dataset.index
    const photo = this.data.photos[index]
    if (!photo) return
    wx.vibrateShort({ type: 'light' })
    this.setData({
      showMenu: true,
      menuPhoto: {
        ...photo,
        featureIcon: photo.isFeatured ? '⭐' : '☆',
        featureText: photo.isFeatured ? '取消精选' : '标记精选'
      },
      menuIndex: index
    })
  },

  closeMenu() {
    this.setData({ showMenu: false, menuPhoto: null })
  },

  menuAction(e) {
    const action = e.currentTarget.dataset.action
    const photo = this.data.menuPhoto
    this.closeMenu()
    switch (action) {
      case 'associate': this.doAssociate(photo); break
      case 'feature': this.doFeatured(photo); break
      case 'tag': this.doEditTag(photo); break
      case 'delete': this.confirmDelete(photo); break
      case 'multi': this.enterMultiMode(); break
      case 'save': this.doSave(photo); break
    }
  },

  // ======== 单张操作 ========

  doAssociate(photo) {
    wx.navigateTo({
      url: '/pages/teacher/student-picker/student-picker?photo_id=' + photo.id + '&file_path=' + encodeURIComponent(photo.filePath)
    })
  },

  doFeatured(photo) {
    const newVal = !photo.isFeatured
    api.request({
      url: '/photos/' + photo.id + '/featured',
      method: 'PUT',
      data: { is_featured: newVal }
    }).then(() => {
      const photos = this.data.photos.map(p => {
        if (p.id === photo.id) p.isFeatured = newVal
        return p
      })
      this.setData({ photos })
      wx.showToast({ title: newVal ? '已标记精选' : '取消精选', icon: 'success' })
    }).catch((err) => util.showError(err.message || '操作失败'))
  },

  confirmDelete(photo) {
    wx.showModal({
      title: '确认删除',
      content: '确定要删除这张照片吗？删除后无法恢复。',
      success: (res) => { if (res.confirm) this.doDelete(photo) }
    })
  },

  doDelete(photo) {
    api.request({ url: '/photos/' + photo.id, method: 'DELETE' })
      .then(() => {
        const photos = this.data.photos.filter(p => p.id !== photo.id)
        this.setData({ photos })
        wx.showToast({ title: '已删除', icon: 'success' })
      }).catch((err) => util.showError(err.message || '删除失败'))
  },

  doSave(photo) {
    wx.downloadFile({
      url: photo.url,
      success: (res) => {
        wx.saveImageToPhotosAlbum({
          filePath: res.tempFilePath,
          success: () => wx.showToast({ title: '已保存到相册', icon: 'success' }),
          fail: () => util.showError('保存失败，请检查相册权限')
        })
      }, fail: () => util.showError('下载失败')
    })
  },

  doEditTag(photo) {
    this.setData({
      showTagPicker: true,
      tagPickerPhoto: photo,
      tagOptions: this._buildTagOptions(photo.localTag)
    })
  },

  _buildTagOptions(activeTag) {
    return [
      { key: 'general', label: '日常' },
      { key: 'activity', label: '活动' },
      { key: 'homework', label: '作业' },
      { key: 'meal', label: '餐食' },
      { key: 'daily', label: '生活' },
    ].map(item => ({ ...item, className: item.key === activeTag ? 'active' : '', checked: item.key === activeTag }))
  },

  selectTag(e) {
    const tagKey = e.currentTarget.dataset.key
    const photo = this.data.tagPickerPhoto
    if (!photo) return
    const tags = this._getLocalTags()
    if (tagKey === '') { delete tags[photo.id] }
    else { tags[photo.id] = tagKey }
    this._saveLocalTags(tags)
    const photos = this.data.photos.map(p => {
      if (p.id === photo.id) {
        p.localTag = tagKey
        p.photoTypeLabel = tagKey ? this._typeLabel(tagKey) : (this._typeLabel(p.photoType) || '')
      }
      return p
    })
    this.setData({ photos, showTagPicker: false, tagPickerPhoto: null })
    wx.showToast({ title: tagKey ? '已设为' + this._typeLabel(tagKey) : '已清除标签', icon: 'success' })
  },

  cancelTagPicker() {
    this.setData({ showTagPicker: false, tagPickerPhoto: null })
  },

  // ======== 多选模式 ========

  enterMultiMode() {
    this.setData({ multiMode: true, selectedIds: [], selectedPhotos: [] })
    const photos = this.data.photos.map(p => ({ ...p, selected: false, checkboxClass: '' }))
    this.setData({ photos })
  },

  exitMultiMode() {
    this.setData({ multiMode: false, selectedIds: [], selectedPhotos: [] })
  },

  toggleSelect(e) {
    const index = e.currentTarget.dataset.index
    const photo = this.data.photos[index]
    if (!photo) return
    photo.selected = !photo.selected
    let selectedIds = [...this.data.selectedIds]
    let selectedPhotos = [...this.data.selectedPhotos]
    if (photo.selected) {
      selectedIds.push(photo.id)
      selectedPhotos.push(photo)
    } else {
      selectedIds = selectedIds.filter(id => id !== photo.id)
      selectedPhotos = selectedPhotos.filter(p => p.id !== photo.id)
    }
    this.setData({
      ['photos[' + index + '].selected']: photo.selected,
      ['photos[' + index + '].checkboxClass']: photo.selected ? 'checked' : '',
      selectedIds,
      selectedPhotos
    })
  },

  // ======== 批量操作 ========

  batchAssociate() {
    if (this.data.selectedIds.length === 0) { util.showError('请先选择照片'); return }
    const ids = this.data.selectedIds.join(',')
    wx.navigateTo({ url: '/pages/teacher/student-picker/student-picker?batch_photo_ids=' + ids })
  },

  batchFeatured() {
    if (this.data.selectedIds.length === 0) { util.showError('请先选择照片'); return }
    const ids = this.data.selectedIds
    wx.showModal({
      title: '批量标记精选',
      content: '确定将选中的 ' + ids.length + ' 张照片标记为精选？',
      success: (res) => {
        if (res.confirm) {
          api.request({ url: '/photos/batch', method: 'POST', data: { operation: 'feature', photo_ids: ids } })
            .then(() => {
              wx.showToast({ title: '已标记 ' + ids.length + ' 张', icon: 'success' })
              this.exitMultiMode()
              this.loadPhotos(true)
            }).catch((err) => util.showError(err.message || '操作失败'))
        }
      }
    })
  },

  batchDelete() {
    if (this.data.selectedIds.length === 0) { util.showError('请先选择照片'); return }
    const ids = this.data.selectedIds
    wx.showModal({
      title: '批量删除',
      content: '确定要删除选中的 ' + ids.length + ' 张照片吗？此操作不可恢复。',
      success: (res) => {
        if (res.confirm) {
          api.request({ url: '/photos/batch', method: 'POST', data: { operation: 'delete', photo_ids: ids } })
            .then(() => {
              wx.showToast({ title: '已删除 ' + ids.length + ' 张', icon: 'success' })
              this.exitMultiMode()
              this.loadPhotos(true)
            }).catch((err) => util.showError(err.message || '操作失败'))
        }
      }
    })
  },

  clearSelection() {
    const photos = this.data.photos.map(p => ({ ...p, selected: false, checkboxClass: '' }))
    this.setData({ photos, selectedIds: [], selectedPhotos: [] })
  },

  goUpload() {
    wx.navigateTo({ url: '/pages/teacher/photo/photo' })
  }
})
