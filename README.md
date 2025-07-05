# Instagram-Telegram-API

Instagram-Telegram-API MiniApp is a Django-powered Telegram WebApp that connects with your Instagram account to bring your DMs, profile insights, subscription management, and advanced chat analysis right into Telegram — all in one seamless interface.

---

## 🚀 Features

- 🔐 **Login with Instagram**  
  Securely connect your Instagram account via Telegram.

- 💬 **Chat Viewer**  
  Browse all your Instagram DMs including:
  - Text messages  
  - Voice notes  
  - Posts  
  - Photos  
  - Reels  
  *(Note: Stories are not supported yet.)*

- 📊 **Chat Analysis**  
  View emotional insights and categorized breakdowns of your conversations, available under the **Profile** tab.

- 🧾 **Subscription Management**  
  - View your current plan  
  - Upgrade to new subscription tiers directly through the app

- 📈 **Insights & Trends**  
  Navigate to the **Analysis** page to find:
  - Popular product mentions  
  - Time-based message activity and trends

---

## ⚙️ Built With

- **Backend:** Django  
- **Frontend:** Telegram WebApp + HTML/CSS  
- **Database:** MongoDB (MongoDB Atlas)  
- **Design:** Instagram-style UI optimized for mobile

---

## 🛠️ Installation & Setup

Follow the steps below to set up and run the project locally or on a server using Docker:

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/megachat.git
cd megachat
```
### 2. Create the .env File

In the root directory (same location as manage.py), create a file named .env with the following structure:
DEBUG=False
SECRET_KEY=your_django_secret_key
ALLOWED_HOSTS=0.0.0.0,megachat.ahmafi.ir
TELEGRAM_TOKEN=your_telegram_bot_token
ATLAS_URI=your_mongodb_atlas_connection_string
DB_NAME=your_mongodb_database_name

### 3. Run the App Using Docker

```bash
sudo docker compose up --build
sudo docker compose down --rmi all
```
