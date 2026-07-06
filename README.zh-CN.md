# Comet 邀请码捕获器

一个用于监控 Twitter 并自动捕获 Comet 邀请码的系统。

**Comet** 是由 **Perplexity** 开发的原生 AI 网页浏览器，它彻底改变了人们的网页浏览方式。Comet 并不将 AI 视为独立的聊天机器人，而是将 AI 辅助功能直接整合到浏览体验中，让用户无需在多个标签页或应用程序之间频繁切换，即可进行搜索、页面总结、回答问题以及完成复杂任务。通过结合实时网页访问与智能推理能力，Comet 的目标是将研究、信息检索以及日常网页工作流程的速度和效率大幅提升。

## 项目结构

```
├── backend/          # FastAPI 后端服务
├── frontend/         # TypeScript/Vite 前端
├── monitor/          # 后台监控服务
├── config/           # 环境配置文件
└── setup_env.sh      # 环境配置脚本
```

## 安装准备

1. 运行配置脚本以创建 Python 虚拟环境：
   ```bash
  ./setup_env.sh
   ```

2. 安装前端依赖项：
   ```bash
   cd frontend
   npm install
   ```

## 开发流程

1. 激活 Python 虚拟环境：
   ```bash
   source venv/bin/activate
   ```

2. 启动后端服务器：
   ```bash
   cd backend
   uvicorn main:app --reload --port 8000
   ```

3. 启动前端开发服务器：
   ```bash
   cd frontend
   npm run dev
   ```

## 配置文件

- 开发环境：`config/development.env`
- 生产环境：`config/production.env`

## 生产环境部署
相关文件：
- Dockerfile - 轻量级容器配置
- docker-compose.yml - 服务编排文件
- nginx.conf - 反向代理配置
- deploy.sh - 一键部署脚本
- deploy/production-setup.md - 完整的部署指南

主要特性：
- 为简化操作使用 SQLite（无需外部数据库）
- 后端采用单个 Docker 容器
- Nginx 负责提供前端服务并代理 API 请求
- 可通过./deploy.sh 手动进行更新
- 已针对 comethunter.skywu.me 进行了配置

部署步骤：
1. 将项目上传至您的 Linux 服务器
2. 运行./deploy.sh
3. 使用 certbot --nginx -d comethunter.skywu.me 添加 SSL 证书
