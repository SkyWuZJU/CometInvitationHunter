# Comet 邀请码捕获器

一个用于监控 Twitter 并自动抓取 Comet 邀请码的系统。

**Comet** 是由 **Perplexity** 开发的一款原生支持人工智能的网页浏览器，它将人工智能直接整合到浏览体验中，从而让搜索、研究以及日常网络任务变得更加快速高效。


## 项目结构

```
├── backend/          # FastAPI 后端服务
├── frontend/         # TypeScript/Vite 前端
├── monitor/          # 后台监控服务
├── config/           # 环境配置文件
└── setup_env.sh      # 环境设置脚本
```

## 设置环境

1. 运行设置脚本以创建 Python 虚拟环境：
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
- 为简化操作而使用 SQLite（无需外部数据库）
- 后端采用单个 Docker 容器
- Nginx 负责托管前端页面并代理 API 请求
- 可通过./deploy.sh 手动进行更新
- 已针对 comethunter.skywu.me 进行了配置

部署步骤：
1. 将项目上传至您的 Linux 服务器
2. 运行./deploy.sh
3. 使用 certbot --nginx -d comethunter.skywu.me 添加 SSL 证书
