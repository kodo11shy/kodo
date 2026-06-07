// 系统设置页
const api = require('../../../utils/api')
const util = require('../../../utils/util')

Page({
  data: {
    config: {},
    originalConfig: {},
    loading: false,
    saving: false,
    saved: false,
    hasUnsavedChanges: false,
    // 自定义收费（纯自定义，不含 is_standard 标记的）
    customFees: [],
    originalCustomFees: [],
    // 标准收费覆盖项（用户编辑过名称/单位/说明的标准项）
    standardOverrides: [],
    originalStandardOverrides: [],
    // 统一收费列表（用于展示）
    unifiedFeeList: [],
    showFeeForm: false,
    editingItem: null,     // 当前编辑的 unifiedFeeList 项（用于定位）
    feeForm: { name: '', amount: '', unit: '元/月', description: '' }
  },

  onLoad() {
    this.loadConfig()
  },

  loadConfig() {
    this.setData({ loading: true })
    const keys = 'school_name,welcome_message,tuition_fee,meal_fee,material_fee,fee_custom_items,contact_wechat,contact_phone'
    api.request({ url: '/config', data: { keys } })
      .then((data) => {
        // 把 fee_custom_items 拆分为标准覆盖项 + 纯自定义项
        const allItems = this.parseCustomFees(data.fee_custom_items)
        const standardOverrides = allItems.filter(f => f.is_standard === true) || []
        const customFees = allItems.filter(f => f.is_standard !== true) || []

        const normalizedConfig = {
          school_name: '',
          welcome_message: '',
          tuition_fee: '0',
          meal_fee: '0',
          material_fee: '0',
          fee_custom_items: '',
          contact_wechat: '',
          contact_phone: '',
          ...data
        }

        this.setData({
          config: { ...normalizedConfig },
          originalConfig: { ...normalizedConfig },
          standardOverrides,
          originalStandardOverrides: JSON.parse(JSON.stringify(standardOverrides)),
          customFees,
          originalCustomFees: JSON.parse(JSON.stringify(customFees)),
          hasUnsavedChanges: false
        })
        this.buildUnifiedFeeList()
      })
      .catch(() => util.showError('加载失败'))
      .finally(() => this.setData({ loading: false }))
  },

  // 解析自定义收费 JSON
  parseCustomFees(str) {
    if (!str) return []
    try {
      const items = JSON.parse(str)
      return Array.isArray(items) ? items : []
    } catch {
      return []
    }
  },

  // ── 统一收费列表 ──

  // 构建统一收费列表（标准 + 自定义，归零项隐藏）
  buildUnifiedFeeList() {
    const { config, standardOverrides, customFees } = this.data

    // 标准收费基础定义
    const standardDefs = [
      { key: 'tuition_fee', name: '托管费', unit: '元/月', description: '周一至周五放学后' },
      { key: 'meal_fee', name: '餐费', unit: '元/月', description: '每日一餐两点' },
      { key: 'material_fee', name: '材料费', unit: '元/学期', description: '学习材料' }
    ]

    // 标准项：应用覆盖项中的名称/单位/说明，金额从 config 读取
    const standardItems = standardDefs.map(def => {
      const override = standardOverrides.find(o => o.key === def.key)
      const amount = config[def.key] || '0'
      return {
        _id: 'std_' + def.key,
        key: def.key,
        name: override ? override.name : def.name,
        amount: amount,
        unit: override ? override.unit : def.unit,
        description: override ? override.description : def.description,
        isStandard: true,
        isOverridden: !!override
      }
    }).filter(f => {
      // 归零隐藏
      const amt = parseFloat(f.amount)
      return !isNaN(amt) && amt > 0
    })

    // 纯自定义项
    const customItems = customFees.map((f, i) => ({
      ...f,
      _id: 'custom_' + i,
      isStandard: false
    }))

    this.setData({ unifiedFeeList: [...standardItems, ...customItems] })
  },

  onFieldChange(e) {
    const field = e.currentTarget.dataset.field
    const value = e.detail.value
    this.setData({ ['config.' + field]: value, saved: false }, () => {
      this.setData({ hasUnsavedChanges: this.hasChanges() })
    })
    // 标准费用金额变化时重建列表（可能触发归零隐藏/显示）
    if (['tuition_fee', 'meal_fee', 'material_fee'].includes(field)) {
      this.buildUnifiedFeeList()
    }
  },

  saveConfig() {
    // 合并标准覆盖项 + 纯自定义项
    const mergedCustomFees = [...this.data.standardOverrides, ...this.data.customFees]

    const dataToSave = { ...this.data.config }
    dataToSave.fee_custom_items = JSON.stringify(mergedCustomFees)

    this.setData({ saving: true })
    api.request({
      url: '/config',
      method: 'PUT',
      data: { values: dataToSave }
    }).then(() => {
      util.showSuccess('保存成功')
      this.setData({
        saved: true,
        originalConfig: { ...dataToSave },
        originalStandardOverrides: JSON.parse(JSON.stringify(this.data.standardOverrides)),
        originalCustomFees: JSON.parse(JSON.stringify(this.data.customFees)),
        hasUnsavedChanges: false
      })
      this.buildUnifiedFeeList()

      // 通知首页立即刷新
      const pages = getCurrentPages()
      const homePage = pages.find(p => p.route === 'pages/index/index')
      if (homePage && homePage.loadHomepage) {
        homePage.loadHomepage()
      }
    }).catch((err) => {
      util.showError(err.message || '保存失败')
    }).finally(() => this.setData({ saving: false }))
  },

  hasChanges() {
    const c = this.data.config
    const o = this.data.originalConfig
    const stdChanged = c.school_name !== o.school_name ||
      c.welcome_message !== o.welcome_message ||
      c.tuition_fee !== o.tuition_fee ||
      c.meal_fee !== o.meal_fee ||
      c.material_fee !== o.material_fee ||
      c.contact_wechat !== o.contact_wechat ||
      c.contact_phone !== o.contact_phone

    const overridesChanged = JSON.stringify(this.data.standardOverrides) !== JSON.stringify(this.data.originalStandardOverrides)
    const feesChanged = JSON.stringify(this.data.customFees) !== JSON.stringify(this.data.originalCustomFees)
    return stdChanged || overridesChanged || feesChanged
  },

  // ── 收费项目编辑 ──

  openAddFee() {
    this.setData({
      showFeeForm: true,
      editingItem: null,
      feeForm: { name: '', amount: '', unit: '元/月', description: '' }
    })
  },

  openEditFee(e) {
    const idx = e.currentTarget.dataset.index
    const item = this.data.unifiedFeeList[idx]
    this.setData({
      showFeeForm: true,
      editingItem: item,
      feeForm: {
        name: item.name || '',
        amount: item.amount || '',
        unit: item.unit || '元/月',
        description: item.description || ''
      }
    })
  },

  closeFeeForm() {
    this.setData({ showFeeForm: false })
  },

  onFeeFieldChange(e) {
    const field = e.currentTarget.dataset.field
    const value = e.detail.value
    this.setData({ ['feeForm.' + field]: value })
  },

  saveFeeItem() {
    const form = this.data.feeForm
    if (!form.name.trim()) {
      util.showError('请输入收费项目名称')
      return
    }
    if (!form.amount || parseFloat(form.amount) <= 0) {
      util.showError('请输入有效金额')
      return
    }

    const item = this.data.editingItem

    if (item && item.isStandard) {
      // ── 编辑标准收费项 ──
      const key = item.key

      // 更新金额到 config
      this.setData({ ['config.' + key]: form.amount, saved: false })

      // 更新或创建标准覆盖项（保存名称/单位/说明的变更）
      let newOverrides = [...this.data.standardOverrides]
      const existingIdx = newOverrides.findIndex(o => o.key === key)
      const overrideEntry = {
        key: key,
        name: form.name.trim(),
        amount: form.amount,
        unit: form.unit || '元/月',
        description: form.description || '',
        is_standard: true
      }

      if (existingIdx >= 0) {
        newOverrides[existingIdx] = overrideEntry
      } else {
        newOverrides.push(overrideEntry)
      }

      this.setData({ standardOverrides: newOverrides })

    } else if (item && !item.isStandard) {
      // ── 编辑自定义收费项 ──
      // 从 _id 中提取 customFees 中的下标
      const customIdx = parseInt(item._id.replace('custom_', ''))
      const newFees = [...this.data.customFees]
      newFees[customIdx] = {
        name: form.name.trim(),
        amount: form.amount,
        unit: form.unit || '元/月',
        description: form.description || ''
      }
      this.setData({ customFees: newFees })

    } else {
      // ── 新增自定义收费项 ──
      const newFees = [...this.data.customFees]
      newFees.push({
        name: form.name.trim(),
        amount: form.amount,
        unit: form.unit || '元/月',
        description: form.description || ''
      })
      this.setData({ customFees: newFees })
    }

    this.setData({
      showFeeForm: false,
      hasUnsavedChanges: true
    })
    this.buildUnifiedFeeList()
  },

  deleteFeeItem(e) {
    const idx = e.currentTarget.dataset.index
    const item = this.data.unifiedFeeList[idx]
    if (item.isStandard) return  // 标准项不能删除

    const customIdx = parseInt(item._id.replace('custom_', ''))
    const target = this.data.customFees[customIdx]

    wx.showModal({
      title: '确认删除',
      content: '确定要删除"' + target.name + '"吗？',
      success: (res) => {
        if (res.confirm) {
          const newFees = [...this.data.customFees]
          newFees.splice(customIdx, 1)
          this.setData({ customFees: newFees, hasUnsavedChanges: true })
          this.buildUnifiedFeeList()
        }
      }
    })
  },

  // ── 其他 ──

  doLogout() {
    wx.showModal({
      title: '退出登录',
      content: '确定要退出吗？',
      success: (res) => {
        if (res.confirm) {
          const app = getApp()
          app.logout()
        }
      }
    })
  },

  about() {
    wx.showModal({
      title: '关于',
      content: '智慧托班管理系统 v1.0\n用心陪伴每一个孩子',
      showCancel: false
    })
  }
})
