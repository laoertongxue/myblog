#!/bin/bash
# 12Lab 服务器初始化脚本
# 创建版本化部署目录，配置 Caddy

set -e

echo "=== 创建部署目录 ==="
mkdir -p /var/www/12lab.cn/releases
mkdir -p /var/www/12lab.cn/current

echo "=== 复制当前 Caddy 默认页面到 current ==="
cp -r /usr/share/caddy/* /var/www/12lab.cn/current/ 2>/dev/null || true

echo "=== 更新 Caddy 配置 ==="
caddy validate --config "$(dirname "$0")/Caddyfile" --adapter caddyfile
install -m 644 "$(dirname "$0")/Caddyfile" /etc/caddy/Caddyfile

echo "=== 重载 Caddy ==="
systemctl reload caddy

echo "=== 验证 Caddy 状态 ==="
systemctl status caddy --no-pager | head -5

echo "=== 验证网站访问 ==="
curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" https://12lab.cn/

echo "=== 完成 ==="
echo "部署目录: /var/www/12lab.cn/"
echo "  releases/  - 版本化发布目录"
echo "  current    - 当前版本（符号链接或直接目录）"
echo "Caddy 根目录: /var/www/12lab.cn/current"
