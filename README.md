# AutoWiper 🧹

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](LICENSE)
[![Pyrogram](https://img.shields.io/badge/Pyrogram-v2.0-red)](https://docs.pyrogram.org/)
[![Made with Python](https://img.shields.io/badge/Made%20with-Python-37766B.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Deploy on Koyeb](https://img.shields.io/badge/Deploy-Koyeb-00C7B7)](https://www.koyeb.com/)
[![Web App Support](https://img.shields.io/badge/Web%20App-Enabled-brightgreen)](https://github.com/PIROXTG/AutoWiper/tree/WebApp)

> **A lightweight Telegram auto-cleaner bot with web dashboard** that automatically deletes messages in groups and channels after a set time. Keep your chats **clutter-free, spam-free, and organized** — automatically. Now with **web monitoring dashboard** for cloud hosting!

🔹 **Made by**: [PIROXTG](https://github.com/PIROXTG)  
🔹 **Session Generator**: [@SessionStringZBot](https://t.me/SessionStringZBot) (trusted & secure)  
🔹 **Support & Help**: [@piroxhelorobot](https://t.me/piroxhelorobot)  
🔹 **Web App Branch**: [Web App Support](https://github.com/PIROXTG/AutoWiper/tree/WebApp) (for cloud hosting)

## 🚨 IMPORTANT SECURITY NOTICE

> **⚠️ WARNING**: This bot uses your personal Telegram account session. Improper handling can lead to account compromise.

**NEVER**:
- Fork this repository publicly with your credentials
- Commit `config.py` with real values to any repository
- Share your session string or bot token with anyone

**ALWAYS**:
- ⭐ Star the original repository first
- Use GitHub's **Import repository** feature (not fork)
- Make your imported repository **PRIVATE**
- Use environment variables for deployment
- Keep your credentials secure and private

**DISCLAIMER**: The author is not responsible for any account compromise due to improper credential handling. Use at your own risk.

## ✨ Key Features

✅ **Auto-delete messages** in multiple Telegram groups or channels  
✅ **Per-chat timer control** — set different durations for each chat  
✅ **Web dashboard** — monitor bot status via web interface (koyeb branch)  
✅ **System monitoring** — comprehensive CPU, RAM, disk, and network stats  
✅ **Auto-ping system** — keeps cloud deployments alive  
✅ **Lightweight & fast** — built with [Pyrogram](https://docs.pyrogram.org/) (MTProto API)  
✅ **Userbot + Bot mode** — uses a user session for full message control  
✅ **Scheduled cleanup** — uses APScheduler for reliable timing  
✅ **Remote management** — control via Telegram commands  
✅ **Cloud ready** — optimized for Koyeb, Heroku, Railway, and VPS  
✅ **Production-grade** — graceful shutdown & comprehensive logging

---

## 🌐 Web App Features (Koyeb Branch)

The `koyeb` branch includes additional web application features:

### 📊 Web Dashboard Endpoints
| Endpoint | Description | Access |
|----------|-------------|---------|
| `/` | Main dashboard with bot overview | Public |
| `/health` | Health check API (JSON) | Public |
| `/stats` | Detailed system statistics (JSON) | Public |

### 🔄 Auto-Keep-Alive System
- **Auto-ping**: Pings web server every 2 minutes
- **Prevents sleeping** on free hosting platforms
- **Always-on monitoring** for 24/7 operation

### 📈 Enhanced Monitoring
- **Real-time system stats**: CPU, RAM, disk usage
- **Network monitoring**: Data transfer statistics
- **Process monitoring**: Bot resource usage
- **Load averages**: System performance metrics

---

## 📋 Commands Reference

### Bot Commands (Private Chat)
| Command | Description |
|---------|-------------|
| `/start` | Check if the bot is online |
| `/ping` | Measure bot response latency |
| `/status` | View uptime, active jobs, and system stats |
| `/sysinfo` | Detailed system information (koyeb branch) |

### Userbot Commands (In Monitored Chats)
| Command | Description |
|---------|-------------|
| `/delete` | Force immediate cleanup of old messages |
| `/update` | Pull latest code from GitHub and restart |
| `/restart` | Restart the bot service |
| `/chats` | List all monitored chats and their delete timers |
| `/stats` | Enhanced statistics dashboard (Owner only, koyeb branch) |
| `/webapp` | Web dashboard information (koyeb branch) |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- Git installed on your system
- Telegram **bot token** from [@BotFather](https://t.me/BotFather)
- Telegram **user session string** from [@SessionStringZBot](https://t.me/SessionStringZBot)

### Local Installation (Main Branch)

1. **Clone the repository**
   ```bash
   git clone https://github.com/PIROXTG/AutoWiper.git
   cd AutoWiper
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure the bot (Local Development Only)**
   
   ⚠️ **For local testing only** - Edit `config.py`:
   ```python
   # Telegram API Credentials
   API_ID = 12345678
   API_HASH = "your_api_hash_here"
   BOT_TOKEN = "your_bot_token_here"
   SESSION = "your_user_session_string_here"
   
   # Chat Configuration
   CHAT_IDS = [-1001234567890, -1009876543210]  # Chat IDs to monitor
   
   # Delete Timer Configuration (in seconds)
   ID_DUR = {
       -1001234567890: 3600,     # Delete after 1 hour
       -1009876543210: 7200,     # Delete after 2 hours
       # Use 0 to disable auto-delete for specific chats
   }
   ```
   
   **⚠️ NEVER commit this file with real credentials!**

4. **Run the bot**
   ```bash
   python main.py
   ```

---

## ☁️ Cloud Deployment

### Deploy on Koyeb (Recommended ✅)

Koyeb offers excellent free hosting perfect for AutoWiper with web app support:

⭐ **IMPORTANT**: Always **star** the original repository first!

1. **Import as Private Repository**:
   - Go to GitHub → **Import repository**
   - Clone URL: `https://github.com/PIROXTG/AutoWiper.git`
   - Make it **PRIVATE** (crucial for security)
   - **DO NOT FORK** - Others can see your environment variables if you fork publicly

2. **Switch to Koyeb Branch**:
   ```bash
   git checkout koyeb
   ```
   Or during import, specify branch: `koyeb`

3. **Deploy on Koyeb**:
   - Sign up at [Koyeb](https://www.koyeb.com/)
   - Click **"Create App"** → **"Deploy from Git"**
   - Select your **private** imported repository
   - **Choose branch**: `koyeb` (important!)
   - Choose **Docker** deployment method
   - Set **Service Type**: `Web Service` (for web app support)
   - **Port**: Set to `8080` (default web server port)
   - Add **Environment Variables** (see configuration below)
   - Click **Deploy** 🚀

4. **Access Web Dashboard**:
   - After deployment, you'll get a public URL
   - Visit the URL to see your bot's web dashboard
   - Monitor system stats, uptime, and bot health in real-time

⚠️ **Security Warning**: Never store credentials in public repositories. If you accidentally push sensitive data, immediately rotate all tokens and session strings.

### Alternative Cloud Platforms

| Platform | Branch | Service Type | Notes |
|----------|---------|--------------|-------|
| **Koyeb** | `koyeb` | Web Service | ✅ Best choice, free tier, web dashboard |
| **Railway** | `koyeb` | Web Service | Supports web apps, paid after trial |
| **Heroku** | `koyeb` | Web Dyno | Uses web server, includes `Procfile` |
| **VPS/Server** | `koyeb` | Manual | Full control, SSH access required |

### Local Development with Web App
For local testing with web features:
```bash
git checkout koyeb
pip install -r requirements.txt  # Includes aiohttp, psutil
python main.py
```
Access dashboard at: `http://localhost:8080`

---

## ⚙️ Configuration Guide

### Environment Variables (Production)
For cloud deployment, set these environment variables:

#### Required Variables
```bash
API_ID=your_api_id
API_HASH=your_api_hash
BOT_TOKEN=your_bot_token
SESSION=your_session_string
CHAT_IDS=[-1001234567890,-1009876543210]
```

#### Optional Variables (Koyeb Branch)
```bash
PORT=8080                    # Web server port (auto-detected on most platforms)
ID_DUR={-1001234567890:3600} # Delete timers in JSON format
```

### Dependencies by Branch

#### Main Branch (`requirements.txt`)
```
pyrotgfork==2.1.35
tgcrypto==1.2.5
APScheduler==3.10.4
```

#### Koyeb Branch (`requirements.txt`)
```
pyrotgfork==2.1.35
tgcrypto==1.2.5
APScheduler==3.10.4
aiohttp==3.9.1              # Web server support
psutil==5.9.6               # System monitoring
```

### Timer Configuration Examples
```python
ID_DUR = {
    -1001234567890: 300,      # 5 minutes
    -1009876543210: 1800,     # 30 minutes
    -1007654321098: 3600,     # 1 hour
    -1005432109876: 86400,    # 24 hours
    -1003210987654: 0,        # Disabled (no auto-delete)
}
```

---

## 🌐 Web Dashboard Guide (Koyeb Branch)

### Dashboard Features
- **📊 Real-time Monitoring**: System stats, uptime, active jobs
- **🖥️ System Health**: CPU, RAM, disk usage with visual indicators
- **📈 Performance Metrics**: Load averages, network statistics
- **🤖 Bot Status**: Connection status, monitored chats, queue size
- **📱 Mobile Friendly**: Responsive design for all devices

### API Endpoints
Perfect for monitoring integrations:

```bash
# Health check (for uptime monitoring)
GET /health
{
  "status": "healthy",
  "uptime": "2:30:45",
  "active_jobs": 15,
  "monitored_chats": 3,
  "bot_running": true,
  "user_running": true
}

# Detailed statistics
GET /stats
{
  "system": {
    "cpu_percent": 15.2,
    "memory_percent": 45.8,
    "disk_percent": 32.1,
    "load_avg": [0.8, 0.9, 0.7]
  },
  "bot_status": {
    "bot_connected": true,
    "user_connected": true,
    "scheduler_running": true
  }
}
```

### Monitoring Integration
Use the `/health` endpoint with:
- **UptimeRobot**: HTTP keyword monitoring
- **Pingdom**: Uptime monitoring
- **StatusCake**: Performance monitoring
- **Custom scripts**: Automated health checks

---

## 🔐 Security & Best Practices

### Security Guidelines
- **⚠️ CRITICAL**: Never fork this repository publicly - use GitHub's **Import** feature instead
- Always make your repository **PRIVATE** when importing
- **Never commit** `config.py` with real credentials to any repository
- Use **environment variables only** for production deployments
- **Use HTTPS only** for web dashboard access in production
- If credentials are accidentally exposed, immediately:
  1. Revoke the bot token via @BotFather
  2. Generate a new session string
  3. Delete and recreate the compromised repository
- **DISCLAIMER**: The repository owner is not responsible for compromised accounts due to improper handling of credentials

### Important Notes
- The bot requires **delete message permissions** in target chats
- **Pinned messages** are preserved and won't be deleted
- Only messages older than the specified duration are removed
- The bot uses a user account session for broader permissions
- **Web dashboard** is public by default - no sensitive data is displayed

---

## 🛠️ Troubleshooting

### Common Issues

**Bot not deleting messages?**
- Ensure the user account has admin/delete permissions
- Check if chat IDs are correct (negative numbers for groups/channels)
- Verify the session string is valid

**Web dashboard not loading? (Koyeb branch)**
- Check if you're using the correct branch (`koyeb`)
- Verify `PORT` environment variable is set correctly
- Ensure platform supports web services
- Check deployment logs for aiohttp errors

**Connection errors?**
- Check your internet connection
- Verify API credentials are correct
- Ensure Telegram isn't blocked in your region

**Bot stops working on free hosting?**
- Make sure you're using the `koyeb` branch (has auto-ping)
- Verify web service is properly configured
- Check if platform requires keep-alive requests

**Deployment fails?**
- Ensure you're using the correct branch for your platform
- Check all required environment variables are set
- Verify `requirements.txt` matches your branch

---

## 🤝 Support & Contributing

### Get Help
- 🐛 **Bug Reports**: [Open an issue](https://github.com/PIROXTG/AutoWiper/issues)
- 💬 **Support Chat**: [@piroxhelorobot](https://t.me/piroxhelorobot)
- 📖 **Documentation**: Check this README and inline comments
- 🌐 **Web Dashboard Issues**: Specify if you're using `koyeb` branch

### Contributing
Contributions are welcome! Please:
1. Fork the repository
2. Choose the appropriate branch (`main` for core features, `koyeb` for web features)
3. Create a feature branch
4. Make your changes
5. Submit a pull request

Areas for improvement:
- **Web dashboard enhancements**: Better UI, more metrics
- **Mobile optimization**: Improved responsive design
- **Security features**: Authentication, rate limiting
- **Performance optimizations**: Caching, database integration
- **Additional hosting guides**: More platform-specific instructions

---

## 📚 Technical Details

### Architecture Comparison

#### Main Branch
- **Core Features**: Message deletion, scheduling, basic monitoring
- **Dependencies**: Pyrogram, APScheduler
- **Deployment**: VPS, worker processes

#### Koyeb Branch  
- **Enhanced Features**: Web dashboard, system monitoring, auto-ping
- **Additional Dependencies**: aiohttp (web server), psutil (system stats)
- **Deployment**: Web services, cloud platforms with HTTP support
- **Keep-Alive**: Built-in ping system for free hosting platforms

### Built With
- **[Pyrogram v2.0](https://docs.pyrogram.org/)** - MTProto API framework
- **[APScheduler](https://apscheduler.readthedocs.io/)** - Task scheduling
- **[aiohttp](https://docs.aiohttp.org/)** - Async HTTP server (koyeb branch)
- **[psutil](https://psutil.readthedocs.io/)** - System monitoring (koyeb branch)
- **Python 3.8+** - Core language

### Performance Notes
- **Memory Usage**: ~50-100MB depending on monitored chats
- **CPU Usage**: Minimal (~1-5% on modern systems)
- **Network**: Low bandwidth usage, periodic API calls
- **Web Server**: Lightweight HTTP server, <1MB additional memory

---

## 📄 License

This project is licensed under the **GNU Affero General Public License v3.0 (AGPL-3.0)** - see the [LICENSE](LICENSE) file for details.

🔒 **Important**: Any modifications, forks, or derivative works must also be released under AGPL-3.0 and publicly share their source code if deployed or made accessible over a network.

---

## 🙏 Acknowledgments

- **[Pyrogram](https://docs.pyrogram.org/)** - Excellent MTProto API framework
- **[@SessionStringZBot](https://t.me/SessionStringZBot)** - Trusted session string generator
- **[Koyeb](https://www.koyeb.com/)** - Excellent free cloud hosting with web support
- **[aiohttp](https://docs.aiohttp.org/)** - Robust async HTTP framework
- **Community** - Thanks to all users and contributors!

---

## 🎯 Quick Deploy Buttons

### Koyeb (Web App Support)
[![Deploy to Koyeb](https://img.shields.io/badge/Deploy%20to-Koyeb-00C7B7?style=for-the-badge&logo=koyeb)](https://app.koyeb.com/deploy?type=git&repository=your-private-repo&branch=koyeb&name=autowiper-bot)

### Railway (Web App Support)  
[![Deploy on Railway](https://img.shields.io/badge/Deploy%20on-Railway-4f0bd8?style=for-the-badge&logo=railway)](https://railway.app/new/template?template=your-template&branch=koyeb)

### Heroku (Web App Support)
[![Deploy to Heroku](https://img.shields.io/badge/Deploy%20to-Heroku-430098?style=for-the-badge&logo=heroku)](https://heroku.com/deploy?template=your-private-repo&branch=koyeb)

*Note: Replace template URLs with your private repository*

---

<div align="center">

**🚀 AutoWiper - Keeping your Telegram chats clean, one message at a time.**

**🌐 Now with Web Dashboard Support for Better Monitoring!**

[⭐ Star this repo](https://github.com/PIROXTG/AutoWiper) • [📱 Main Branch](https://github.com/PIROXTG/AutoWiper) • [🌐 Koyeb Branch](https://github.com/PIROXTG/AutoWiper/tree/WebApp) • [📢 Join Support](https://t.me/piroxbots)

</div>