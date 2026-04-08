# 📄 Naukri Resume Auto-Updater

Automates the process of updating your resume on [Naukri.com](https://www.naukri.com) using Playwright. Keeping your resume "fresh" on Naukri improves its visibility to recruiters.

---

## 🚀 Features

- Automatically logs into your Naukri account
- Navigates to your profile page
- Clicks the **"Update Resume"** button to refresh your resume's last-updated timestamp
- Supports credentials via CLI arguments

---

## 🛠️ Prerequisites

- Python 3.8+
- [Playwright for Python](https://playwright.dev/python/)

---

## 📦 Installation

**1. Clone the repository**

```bash
git clone https://github.com/ManojKumar1603/Update-Naukari-Profile.git
cd naukri-resume-updater
```

**2. Install dependencies**

```bash
pip install playwright
```

**3. Install Playwright browsers**

```bash
playwright install chromium
```

---

## ▶️ Usage

Run the script by passing your Naukri credentials as arguments:

```bash
python naukri_updater.py --username "your-email@example.com" --password "YourPassword"
```

### Arguments

| Argument | Required | Description |
|---|---|---|
| `--username` | ✅ Yes | Your Naukri registered email address |
| `--password` | ✅ Yes | Your Naukri account password |

---

## 📁 Project Structure

```
naukri-resume-updater/
│
├── naukri_updater.py   # Main script
└── README.md           # Project documentation
```

---

## ⚙️ How It Works

1. Launches a Chromium browser window
2. Navigates to the Naukri login page
3. Fills in your credentials and submits the login form
4. Waits for the profile page to load
5. Clicks the **"Update Resume"** button
6. Waits 20 seconds to ensure the action completes
7. Closes the browser

---

## 🔒 Security Notes

- **Never hardcode your credentials** in the script. Always pass them via CLI arguments or environment variables.
- Consider using a `.env` file with a library like `python-dotenv` for managing credentials locally.
- Add `.env` to your `.gitignore` to avoid accidentally committing sensitive data.

---

## 🤖 Automate with Cron (Linux/macOS)

To run the script daily at 9 AM:

```bash
crontab -e
```

Add this line:

```
0 9 * * * /usr/bin/python3 /path/to/naukri_updater.py --username "your-email@example.com" --password "YourPassword"
```

---

## 📋 Example

```bash
python naukri_updater.py --username "abcd123@gmail.com" --password "MySecurePass@123"
```

---

## 🐛 Troubleshooting

| Issue | Fix |
|---|---|
| `Timeout` error on login | Check your credentials or try running with `headless=False` to debug |
| Browser not found | Run `playwright install chromium` |
| Element not found | Naukri may have updated their UI; inspect the page and update selectors |

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

---

## 🙌 Contributing

Pull requests are welcome! For major changes, please open an issue first to discuss what you'd like to change.
