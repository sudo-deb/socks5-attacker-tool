

# 🔥 LOST SOCKS5 TOOL

A high-performance HTTP load testing tool with SOCKS5 proxy support. Test your own web server's resilience with concurrent connections through multiple proxies.

## ⚠️ Disclaimer

**This tool is for educational and authorized testing purposes only.** Only use it on servers you own or have explicit permission to test. Unauthorized testing against third-party servers may violate laws and terms of service.

## 🚀 Features

- ✅ **SOCKS5 Proxy Support** - Route traffic through multiple proxies
- ✅ **Concurrent Connections** - Adjustable parallelism for high load
- ✅ **Real-time Monitoring** - Live request log with color-coded responses
- ✅ **HTTP Status Filtering** - Logs only HTTP 200 (green) and HTTP 500 (magenta)
- ✅ **Progress Tracking** - Visual progress indicator during attack
- ✅ **Round-based Testing** - Continuous testing with configurable delays

## 📋 Requirements

```
aiohttp
aiohttp-socks
colorama
tqdm
rich
cython (optional, for compilation)
```

https://github.com/user-attachments/assets/c82cf493-0b4e-4004-8a4d-1304c32207f6

# ▶️ Installation

Install with:
```bash
pip install -r requirements.txt
```

### Proxy Configuration

Create a `proxies.txt` file with one proxy per line:

```
socks5://127.0.0.1:1080
```


## 🖥️ Interface

```
╔══════════════════════════════════════════════════════════════╗
║                    🚀 ATTACK INITIALIZED 🚀                  ║
╠══════════════════════════════════════════════════════════════╣
║  🎯 Target:         https://example.com                      ║
║  🔥 Proxies:        26     proxies active                    ║
║  ⚡ Concurrency:    10     parallel connections              ║
║  📊 Total Req:      2600   requests to send                  ║
║  ⏱️  Rate Limit:   25 proxy/sec                             ║
╚══════════════════════════════════════════════════════════════╝

Attacking: 150/2600 (5.8%)

┌──────────────────── 🔥 Live Request Log ────────────────────┐
│                                                              │
│ ⚠️  [05:00:51] Proxy 6-97: HTTP 500                          │
│ ⚠️  [05:00:51] Proxy 6-98: HTTP 500                          │
│ ✅ [05:00:51] Proxy 10-12: HTTP 200                          │
│ ⚠️  [05:00:51] Proxy 6-99: HTTP 500                          │
│ ...                                                          │
└──────────────────────────────────────────────────────────────┘
```

## 🎨 Color Coding

| Color | Meaning |
|-------|---------|
| 🟢 Green | HTTP 200 - Success |
| 🟣 Magenta | HTTP 500 - Server Error |
| 🔴 Red | Other errors (not shown in live log) |

## ⚙️ Configuration Options

| Setting | Default | Description |
|---------|---------|-------------|
| Concurrency | 10 | Simultaneous proxy connections |
| Requests per Proxy | 100 | Requests sent per proxy |
| Rate Limit | 25/sec | Max proxies initiated per second |
| Timeout | 10s | Request timeout |
| Max Logs | 10 | Rolling log buffer size |

## 🛑 Stopping the Tool

Press `Ctrl+C` at any time to stop the current round. The tool will complete the current batch before exiting.

## 📊 Results

After each round, a summary is displayed:

```
╔══════════════════════════════════════════════════════════════╗
║                    📊 ATTACK COMPLETE 📊                     ║
╠══════════════════════════════════════════════════════════════╣
║  ✅ Success:        1500     requests                        ║
║  ❌ Failed:         100     requests                        ║
║  📈 Success Rate:   93.8%                                  ║
║  ⏱️  Total Time:    45.2s                                  ║
║  ⚡ Avg Response:   0.123s                                  ║
║  🚀 RPS:            35.4 req/s                              ║
╚══════════════════════════════════════════════════════════════╝
```

## 🔧 Troubleshooting

### Proxies not working?
- Verify proxy format in `proxies.txt`
- Check proxy connectivity independently
- Ensure SOCKS5 proxies support your target protocol

### No live requests showing?
- Only HTTP 200 and 500 responses are logged
- Other responses and errors are counted but not displayed
- Check proxy health and target server status

### Screen flickering on resize?
- Use fullscreen terminal for best experience
- Avoid resizing terminal during operation

## 📝 License

This tool is provided as-is for educational purposes. Use responsibly and only on systems you own or have permission to test.

## 🤝 Credits

Built with:
- [aiohttp](https://docs.aiohttp.org/) - Async HTTP client
- [aiohttp-socks](https://github.com/romis2012/aiohttp-socks) - SOCKS proxy support
- [Rich](https://rich.readthedocs.io/) - Terminal formatting
- [Colorama](https://github.com/tartley/colorama) - Cross-platform colors


# 🌐 Contact : 

Discord Server : https://discord.gg/VWzxAcfmTv
