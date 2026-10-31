# WebSocket 僵尸连接诊断案例

## 症状

用户在飞书群发送消息，机器人完全不回复。DM 消息正常。`require_mention: false` 配置正确。

## 时间线（2026-07-14 排查）

| 时间 | 事件 |
|------|------|
| 7/13 10:23:41 | 群里 `/restart`，gateway 重启并重连 WS |
| 7/13 10:23:47 | Lark SDK 连接成功 `conn_id=7661832622675250125` |
| 7/13 10:23 ~ 21:05 | 正常运行，群消息正常收发 |
| 7/13 21:15 | 最后一条群回复发出 |
| 7/13 22:16 | Agent cache idle-TTL evict（正常） |
| 7/14 04:03 | Session expiry 清理（正常 daily reset） |
| 7/14 10:48 | 用户 DM "群聊里挂了？" — **这是 13h+ 后的第一条收到消息** |

## 关键发现

1. **`gateway.log` 中 7/13 21:15 到 7/14 10:48 之间零条 raw message**（群或 DM）
2. **`gateway_state.json` 显示 `connected`，`updated_at` 停留在 7/13 10:23:47**（连接建立时间，之后未变）
3. **Lark SDK 无 `receive message loop exit` 日志** — SDK 认为自己仍在连接中
4. **历史模式：** WS 每 15-19h 断一次（`no close frame received or sent`），但这次断连检测失败了

## 诊断命令速查

```bash
PROFILE=<你的 hermes profile 目录>

# 确认消息是否到达 gateway
grep "关键词" $PROFILE/logs/gateway.log

# 查看 Lark SDK WS 生命周期
grep "\[Lark\]" $PROFILE/logs/gateway.log

# 检查 gateway_state 的 updated_at（僵尸连接的关键信号）
cat $PROFILE/gateway_state.json | python3 -m json.tool | grep -A5 feishu

# 查看长时间段内是否有任何 raw message
awk '/2026-07-13 21:15/,/2026-07-14 10:48/' $PROFILE/logs/gateway.log | grep "raw message"
```

## 修复

```
在群里发 /restart → gateway 重连 WS → 恢复正常
```

## 根因分析

Lark SDK (lark-oapi) 的 WebSocket 实现依赖 TCP 层或框架层的心跳检测来发现断连。当网络中间设备（NAT、防火墙、运营商）静默丢弃了已建立的连接（不发 FIN），如果应用层心跳不够频繁或 SDK 未能正确处理心跳超时，就会出现"假活"连接——socket 看起来还在，但对方已经不在了。
