# Comet Invitation Hunter

这是一个用于监控 Twitter 并自动响应邀请码的系统。

## 项目结构

```
├── backend/          # FastAPI 后端服务
├── frontend/         # 基于 TypeScript/Vite 的前端
├── monitor/          # 后台监控服务
├── config/           # 环境配置文件
└── setup_env.sh      # 环境初始化脚本
```

## 环境配置

1. 运行初始化脚本以创建 Python 虚拟环境：
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

## 配置说明

- 开发环境配置：`config/development.env`
- 生产环境配置：`config/production.env`

## 生产环境部署

相关文件如下：
- Dockerfile – 轻量级容器配置
- docker-compose.yml – 服务编排文件
- nginx.conf – 反向代理配置
- deploy.sh – 一键部署脚本
- deploy/production-setup.md – 完整的部署指南

主要特性：
- 使用 SQLite 简化部署流程（无需外部数据库）
- 后端仅需单个 Docker 容器即可运行
- Nginx 负责提供前端页面并转发 API 请求
- 通过执行 `./deploy.sh` 即可完成手动更新
- 已针对 comethunter.skywu.me 完成配置

部署步骤：
1. 将代码上传至 Linux 服务器
2. 运行 `./deploy.sh`
3. 使用 `certbot --nginx -d comethunter.skywu.me` 配置 SSL 证书
