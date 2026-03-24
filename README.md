# passport-automation
# 🛂 Passport Automation System

A full-stack web application built using **Streamlit** and **MongoDB** to automate passport application processing. This system allows users to submit applications, track status, and enables admins to manage and review applications efficiently.

---

## 🚀 Features

### 👤 User Side

* 📝 New Passport Application Form
* 📸 Upload Passport Photo (Base64 storage)
* 🔍 Track Application Status using Application ID
* ✅ Real-time validation (email, mobile, pincode)

### 👨‍💼 Admin Panel

* 🔐 Secure login authentication
* 📊 Dashboard with statistics
* 🔎 Search & filter applications
* ✅ Approve / Reject / Process applications
* 📥 Export applications as CSV

### 📊 Dashboard

* Total applications count
* Status-wise distribution
* Recent applications overview

---

## 🛠️ Tech Stack

* **Frontend & Backend:** Streamlit
* **Database:** MongoDB
* **Language:** Python
* **Libraries:** Pandas, Pillow, PyMongo

---

## ⚙️ Installation

### 1️⃣ Clone the repository

```bash
git clone https://github.com/your-username/passport-automation-system.git
cd passport-automation-system
```

### 2️⃣ Install dependencies

```bash
pip install -r requirements.txt
```

### 3️⃣ Start MongoDB

Make sure MongoDB is running locally:

```bash
mongodb://localhost:27017/
```

---

## ▶️ Run the Application

```bash
streamlit run app.py
```

---

## 🔐 Environment Variables (Optional)

You can configure these for production:

| Variable         | Description               | Default                    |
| ---------------- | ------------------------- | -------------------------- |
| `MONGO_URI`      | MongoDB connection string | mongodb://localhost:27017/ |
| `ADMIN_PASSWORD` | Admin login password      | Admin@2024                 |

---

## 📁 Project Structure

```
passport-automation-system/
│
├── app.py
├── requirements.txt
└── README.md
```

---

## 📸 Screenshots (Optional)

Add screenshots of:

* Application Form
* Dashboard
* Admin Panel

---

## 💡 Future Enhancements

* 📧 Email notifications
* 📱 SMS alerts
* 🌐 Deployment (Streamlit Cloud / AWS)
* 🔐 Role-based authentication
* 📂 Document uploads (Aadhar, PAN, etc.)

---

## 🤝 Contributing

Feel free to fork this repo and submit pull requests.

---

## 📄 License

This project is open-source and available under the MIT License.

---

## 👩‍💻 Author

**Sandhya Lokesh**

---

## ⭐ Support

If you like this project, give it a ⭐ on GitHub!
