#!/usr/bin/env python3
"""
设计灵感自动抓取器 v2
- 从 GitHub、设计站抓取优秀的移动端 UI 设计
- 分析颜色、排版风格、布局特点
- 推荐最适合当前项目（托班管理系统小程序）的设计参考

使用: python3 design_inspiration_fetcher.py
"""

import json
import re
import os
import subprocess
from datetime import datetime

# ---------- 工具函数 ----------
def curl_get(url, timeout=10):
    """用 curl 命令安全地 fetch URL"""
    try:
        result = subprocess.run(
            ['curl', '-s', '--connect-timeout', str(timeout), '-m', str(timeout+5),
             '-H', 'User-Agent: Mozilla/5.0 (compatible; DesignBot/1.0)',
             url],
            capture_output=True, text=True, timeout=timeout+10
        )
        if result.returncode == 0 and result.stdout:
            return result.stdout
        return None
    except:
        return None

# ---------- 搜索函数 ----------
def search_github_topics():
    """从 GitHub 搜好的 UI 设计和项目"""
    results = []
    
    queries = [
        "wechat miniprogram UI beautiful",
        "微信小程序 模板 设计",
        "mini-program UI kit",
        "weapp demo",
        "education app UI mobile",
        "儿童教育 app 小程序",
        "flutter UI kit education",
        "miniprogram template",
    ]
    
    print("  ├─ 搜索 GitHub 项目...")
    for q in queries:
        url = f"https://api.github.com/search/repositories?q={q.replace(' ', '+')}&sort=stars&order=desc&per_page=3"
        data = curl_get(url)
        if data:
            try:
                d = json.loads(data)
                for r in d.get('items', []):
                    results.append({
                        'source': 'github',
                        'name': r['full_name'],
                        'stars': r['stargazers_count'],
                        'desc': (r.get('description') or '')[:150],
                        'url': r['html_url'],
                        'lang': r.get('language') or '',
                        'topics': r.get('topics', [])
                    })
            except:
                pass
    
    return results

def search_miniprogram_projects():
    """专门搜微信小程序优质项目"""
    results = []
    
    queries = [
        "miniprogram weapp wxapp demo",
        "微信小程序 教育 托管",
        "weapp beautiful UI",
    ]
    
    print("  ├─ 搜索微信小程序项目...")
    for q in queries:
        url = f"https://api.github.com/search/repositories?q={q.replace(' ', '+')}&sort=stars&order=desc&per_page=5"
        data = curl_get(url)
        if data:
            try:
                d = json.loads(data)
                for r in d.get('items', []):
                    results.append({
                        'source': 'miniprogram',
                        'name': r['full_name'],
                        'stars': r['stargazers_count'],
                        'desc': (r.get('description') or '')[:150],
                        'url': r['html_url'],
                        'topics': r.get('topics', [])
                    })
            except:
                pass
    
    return results

def fetch_trending_designs():
    """从 UI 设计灵感站获取热门设计"""
    results = []
    
    # 这些站可以直接访问它们的 RSS 或 API
    targets = [
        # Dribbble 热门
        ("https://dribbble.com/search/education-app-mobile", "dribbble"),
        ("https://dribbble.com/search/kids-app", "dribbble"),
        # Behance 热门
        ("https://www.behance.net/search/projects?search=education+app+UI&sort=appreciations", "behance"),
    ]
    
    print("  ├─ 搜索设计站热门作品...")
    for url, source in targets:
        html = curl_get(url)
        if html:
            # 提取标题
            titles = re.findall(r'<title>([^<]+)', html)
            # 提取链接
            links = re.findall(r'href="(https?://[^"]+/(?:shots|projects)/[^"]+)"', html)
            
            for l in links[:10]:
                results.append({
                    'source': source,
                    'url': l,
                    'title': titles[0] if titles else 'design',
                })
    
    return results

# ---------- 分析函数 ----------
def design_fitness_score(item):
    """给每个设计参考打适合度分（针对托班小程序）"""
    text = json.dumps(item).lower()
    score = 0
    
    # 教育/儿童相关
    edu_keywords = ['教育', 'education', '儿童', 'kid', 'child', 'learn', 'school', 
                    '幼儿园', 'preschool', 'daycare', '托管', '学生', '托班',
                    'classroom', 'teacher', 'attendance']
    for w in edu_keywords:
        if w in text:
            score += 2
    
    # 管理类
    mgmt_keywords = ['管理', 'manage', 'dashboard', 'checkin', '签到', '打卡',
                     'admin', 'attendance']
    for w in mgmt_keywords:
        if w in text:
            score += 1
    
    # 小程序/移动端
    mobile_keywords = ['小程序', 'miniprogram', 'weapp', 'mobile', 'app', '微信',
                       'wechat', 'mini program']
    for w in mobile_keywords:
        if w in text:
            score += 1
    
    # UI/KIT/设计相关
    ui_keywords = ['ui', 'kit', 'template', '设计', '模板', 'style', 'component']
    for w in ui_keywords:
        if w in text:
            score += 1
    
    # 热门程度
    stars = item.get('stars', 0)
    if isinstance(stars, int):
        if stars >= 1000:
            score += 3
        elif stars >= 500:
            score += 2
        elif stars >= 100:
            score += 1
    
    return score

def infer_style(item):
    """推断设计风格"""
    text = json.dumps(item).lower()
    tags = []
    
    style_map = [
        ('简约/干净', ['clean', 'minimal', '简约', '简洁', 'simple', 'minimalist']),
        ('鲜艳/活泼', ['colorful', '鲜艳', 'bright', 'vibrant', 'playful']),
        ('亲和/圆润', ['rounded', '圆角', 'friendly', 'warm', 'soft', 'card']),
        ('深色/高级', ['dark', '深色', 'premium', 'elegant', 'sleek']),
        ('扁平/现代', ['flat', '扁平', 'modern', 'material', 'contemporary']),
        ('卡片式', ['card', '卡片', 'grid']),
        ('数据可视化', ['chart', 'dashboard', '数据', '统计', 'analytics']),
    ]
    
    for tag, keywords in style_map:
        if any(k in text for k in keywords):
            tags.append(tag)
    
    return tags if tags else ['现代']

# ---------- 报告生成 ----------
def generate_report(all_results):
    """生成设计参考报告"""
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    report = f"""# 🎨 设计灵感参考报告

生成时间：{now}
目标：为托班管理系统微信小程序寻找优秀的 UI 设计参考
关注重点：颜色搭配、排版间距、卡片布局、移动端操作流程

---

"""
    
    # 分析并排序
    for item in all_results:
        item['fitness'] = design_fitness_score(item)
        item['style_tags'] = infer_style(item)
    
    all_results.sort(key=lambda x: x.get('fitness', 0), reverse=True)
    
    # TOP 推荐
    top = [r for r in all_results if r.get('fitness', 0) >= 5][:8]
    if top:
        report += "## ⭐ 最佳推荐（最匹配你的项目）\n\n"
        for i, r in enumerate(top, 1):
            name = r.get('name', '未命名')
            stars = r.get('stars', 0)
            desc = r.get('desc', '')
            url = r.get('url', '')
            tags = ', '.join(r.get('style_tags', []))
            fitness = r.get('fitness', 0)
            lang = r.get('lang', '')
            
            report += f"### {i}. {name}\n"
            if stars:
                report += f"   ⭐ **{stars} stars** | 适合度: {'🟢'*min(fitness,5)}{'⚪'*(5-min(fitness,5))} ({fitness}/10)\n"
            if lang:
                report += f"   🛠️ 技术栈: {lang}\n"
            if desc:
                report += f"   📝 {desc}\n"
            if tags:
                report += f"   🏷️ 风格: {tags}\n"
            if url:
                report += f"   🔗 {url}\n"
            report += "\n"
    
    # 其他推荐
    others = [r for r in all_results if r.get('fitness', 0) < 5][:15]
    if others:
        report += "## 📂 更多参考\n\n"
        for r in others:
            name = r.get('name', '未命名')
            stars = r.get('stars', 0)
            desc = r.get('desc', '')
            url = r.get('url', '')
            tags = ', '.join(r.get('style_tags', []))
            
            report += f"- **{name}**"
            if stars:
                report += f" (⭐{stars})"
            if tags:
                report += f" [{tags}]"
            report += "\n"
            if desc:
                report += f"  _{desc}_\n"
            if url:
                report += f"  {url}\n"
            report += "\n"
    
    # 设计建议
    report += """---
## 💡 针对托班小程序的具体设计建议

综合搜索到的优秀项目，以下是对你小程序的实际建议：

### 颜色
- **主色**：温暖橙/暖蓝（不要冷蓝灰），营造信任感和亲和力
- **辅助色**：绿色（签到成功/已到校）、红色（未签到/已离校）
- **背景**：浅灰 #F5F6FA 或纯白 #FFFFFF
- **卡片**：纯白底 + 浅阴影

### 排版
- 标题 17-18px 加粗，正文 14-15px
- 卡片之间留白 16-24px
- 列表项行高至少 44px（手指点击舒适区）
- 圆角 12-16px（亲和力）

### 布局参考
- **签到页** → 参考鹅打卡/微信读书的网格卡片布局
- **学生档案** → 参考通讯录+头像列表
- **工作台首页** → 参考飞书/钉钉的宫格入口布局
- **作业闭环** → 参考 Trello/Notion 的卡片状态流转

### 学习对象
- **微信原生组件** + **Ant Design Mini**（与你的小程序技术栈一致）
- **色板参考**：Linear (紫色系)、Notion (暖灰系)、飞书 (蓝色系)

"""

    return report


# ---------- 主流程 ----------
def main():
    print("🔍 开始搜索设计灵感...\n")
    
    all_results = []
    
    # 并行搜索
    all_results.extend(search_github_topics())
    all_results.extend(search_miniprogram_projects())
    all_results.extend(fetch_trending_designs())
    
    # 去重
    seen = set()
    unique = []
    for r in all_results:
        key = r.get('url', '') or r.get('name', '')
        if key and key not in seen:
            seen.add(key)
            unique.append(r)
    
    print(f"\n✅ 共找到 {len(unique)} 个设计参考\n")
    
    # 生成报告
    report = generate_report(unique)
    
    # 输出
    output_dir = "/home/记事/ObsidianVault/石不语札记/01 - 工作/托班管理系统"
    output_path = os.path.join(output_dir, "设计灵感参考报告.md")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"📄 报告已保存: {output_path}")
    print("\n" + "="*60)
    print("报告摘要：")
    # Print first 1500 chars of report
    lines = report.split('\n')
    for line in lines[:40]:
        print(line)
    print("\n... (完整报告见文件)")
    print("="*60)

if __name__ == '__main__':
    main()
