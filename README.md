# 🎮 GTA RP Family Economy Bot

A personal Discord bot designed to automate **economic reporting** and **quest management** for a GTA Roleplay (RP) family.  
The bot helps organize in-game finances, track weekly results, and manage family quests directly through Discord.

Originally created for a Ukrainian-speaking Discord community, the bot features partial Ukrainian localization and demonstrates modular command handling.

---

## ✨ Features
- 📊 **Automated reporting** – tracks economy data and summarizes weekly results.  
- 🧩 **Quest management** – start, stop, and monitor RP family quests.  
- 📅 **Scheduling system** – timed reminders and event triggers.  
- 📤 **Google Sheets export** – generates weekly economy summaries (`utils/export_sheets.py`).  
- 💾 **Local JSON storage** – persistent data stored as `.json` files instead of a full database.  
- 🌍 **Partial Ukrainian localization** – commands and messages are primarily in Ukrainian.

---

## 📷 Screenshots

### Welcome message
![welcome-message](img/Welcome%20Message.png)

### Report instructions
![report-instructions](img/Report%20instructions.png)

### Command help messages
![help-messages](img/Command%20help%20messages.png)

### Quest reprts examples
![quest-report-examples](img/Quest%20reprts%20examples.png)

### Contribution reports examples
![contribution-reports-examples](img/Contribution%20reports%20examples.png)

### User statistics card
![user-statistics-card](img/User%20statistics%20card.png)

### Weekly quest summary announcement
![weekly-quest-summary-announcement](img/Weekly%20quest%20summary%20announcement.png)

### Automatically issued warning by the Discord bot
![warning](img/Automatically%20issued%20warning%20by%20the%20Discord%20bot.png)

### Family Quests Status Dashboard
[quests-statuses](img/Family%20Quests%20Status%20Dashboard.png)

### Quest Announcement in Discord
[quest-annoncement-1](img/Quest%20Announcement%20in%20Discord.png)

### Quest Announcement in Discord
[quest-annoncement-2](img/Quest%20Announcement%20in%20Discord-1.png)

### Quest Announcement in Discord
[quest-annoncement-3](img/Quest%20Announcement%20in%20Discord-2.png)

### Quest Announcement in Discord
[quest-annoncement-4](img/Quest%20Announcement%20in%20Discord-3.png)

---

## 🧠 Technical Overview
- **Language:** Python 3.12  
- **Framework:** `discord.py`  
- **Configuration:** `config.py`  
- **Data storage:** JSON files in `data/` folder  
- **Exports:** Google Sheets API for weekly reports  
- **Structure:** modular design with cogs and views

---

## ⚙️ Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/gta-rp-economy-bot.git
   cd gta-rp-economy-bot
   ```
2. Install dependencies:
  ```bash
  pip install -r requirements.txt
  ```
3. Configure your bot:
  - Open `config.py`
  - Set your data
  ```python
  DISCORD_TOKEN = "your_token_here"
  COMMAND_PREFIX = "!"
  etc.
  ```
5. Run the bot:
  ```bash
python main.py
```

---

## 🆕 Update — 2025-10-25
- 🧾 **Role change event added:** when a user receives a family role, they are automatically added to the system.
- 🪄 **Quest aliases added:** for example, you can now use alternate names for the quest **“Goods Explosion”** (_orig. “Товарний вибух” — Tovarnyi Vybukh_) - <br>
  `!quest tovarka` (represents Ukrainian command `!квест товарка`),<br>
  `!quest tov` (for `!квест тов`) — this is just to illustrate functionality; in reality, all commands remain in Ukrainian.
- 🗓️ **Improved date parsing:** now recognizes formats like `dd.mm`, `dd.mm.yyyy`, and `dd.mm.yy`, fixing frequent input errors.
- 🧩 **New quests added:** several new family quests have been introduced and integrated into the system.
