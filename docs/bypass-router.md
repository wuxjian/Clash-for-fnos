# 旁路由与透明接管

共享实现由 `upstream.lock` 锁定到 Clash-Manager 1.6.40。旁路由页负责监控，一键配置负责安装/恢复接管规则。

## 一键配置会做什么

- 仅接管所选局域网网卡的 IPv4 流量：Redir 只处理 TCP，TProxy 处理 TCP/UDP。
- 使用本应用独立的 nftables 表 `clash_manager_bypass`，先校验表归属，不覆盖同名外部表。
- 新增转发放行链，并按 `ip route show default` 识别出的 WAN 出接口添加源 NAT（masquerade）。
- 检测到 Docker 的 `DOCKER-USER` 链时，插入带 `clash-manager-bypass` 注释的放行规则；停用时精确删除。
- 可选接管 DNS：把客户端 53 端口重定向到 DNS 设置里已配置的监听端口，不修改 DNS 监听地址。
- 与 TUN 互斥；失败自动回滚；支持“保持启用”，内核重启后核验并恢复。
- 卸载时会调用 helper 清理自有 nftables 表、策略路由和 Docker 放行规则。

## 仍需手动完成的部分

1. **设备网关**：在主路由 DHCP 中把网关改为 NAS 地址，或在每台设备上手动设置。应用不内置 DHCP。
2. **DNS**：先到「设置 → DNS 与解析」启用 Mihomo DNS，并监听 `0.0.0.0:53`（可直接点「载入旁路由 DNS 预设」）。旁路由只做 53 重定向，不会替你改监听地址。
3. **IPv6**：本轮不接管，IPv6 流量仍会绕过代理。
4. **QUIC**：Redir 模式只接管 TCP；需要接管 UDP/QUIC 请选择 TProxy。
5. **其他防火墙**：只处理 nftables 与 Docker 的 `DOCKER-USER`，不接管 iptables-legacy、ufw、firewalld 的转发策略。
6. **断电与崩溃**：nftables 规则不持久，需要应用启动后恢复；没有独立宿主看门狗。

## QUIC 策略

在「订阅配置 → 高级选项 → QUIC 策略」中设置，规则前置注入到所有订阅：

- 国内直连（默认）：`GEOSITE,cn` / `GEOIP,CN` 的 UDP 443 直连。
- 国外拒绝（默认）：其余 UDP 443 使用 `REJECT`，浏览器收到 ICMP 不可达后立即回落 TCP 走代理。
- 国内也可选择拒绝，此时所有 QUIC 一律拒绝。

规则会出现在规则页，可按 identity 单独停用。仅 TProxy/TUN 模式生效。

## 验证与边界

- 页面读到的配置或规则不代表真实客户端已接管，仍需设备流量和真机证据。
- 设备详情中的 TProxy/Redir/TUN 入站连接才是接管证据；命中代理不代表请求成功。
- 系统转发或防火墙处丢包可能不进入 Mihomo，必要时仍需抓包。
- 邻居表只代表“已发现”，不代表设备在线或已设置 NAS 网关。