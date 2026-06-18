/**
 * 全局常量
 * ==========
 * 统一管理所有页面共享的常量，避免各页面硬编码。
 *
 * 使用方式：
 *   const { HOMEWORK_SUBJECTS } = require('../../utils/constants')
 *
 * 如需从后端动态加载，修改 loadFromConfig() 即可，
 * 所有页面统一生效。
 */

// 默认科目（与后端 app.core.homework_rules.ALLOWED_HOMEWORK_SUBJECTS 保持一致）
const HOMEWORK_SUBJECTS = ['语文', '数学']

/**
 * 从后端配置加载科目列表
 * 如果后端未配置，返回默认值
 */
const loadHomeworkSubjects = (config) => {
  if (config && Array.isArray(config.homework_subjects) && config.homework_subjects.length > 0) {
    return config.homework_subjects
  }
  return HOMEWORK_SUBJECTS
}

module.exports = {
  HOMEWORK_SUBJECTS,
  loadHomeworkSubjects
}
