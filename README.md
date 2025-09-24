# VSC - Very Secure Chat 

**VSC** הוא פרויקט לדוגמה של מערכת צ'אטים מאובטחת עם **הצפנה מקצה לקצה (E2E Encryption)**.  
המטרה של הפרויקט היא לשמש כשלד למערכת צ'אט מאובטחת, ובעזרתו העמקתי את ההבנה בנושאים כמו **הצפנה, SQL ו-WebSockets**.

---

##  טכנולוגיות בשימוש

### Backend
- **Python + Flask** – שרת ו־API
- **python-socketio** – ניהול WebSockets
- **MySQL** – ניהול בסיס נתונים בעזרת `mysql-connector`
- **bcrypt** – גיבוב מאובטח לסיסמאות

### Frontend
- **React + Next.js + TailwindCSS** – ממשק המשתמש
- **react-socket-io** – ניהול WebSockets בצד הלקוח

### Cryptography
- **ECDH** – יצירת מפתח משותף להצפנה מקצה לקצה
- **AES-GCM** – הצפנת ההודעות בפועל

---

## ⚙️ איך להריץ?

1. להריץ את השרת (Backend):
```bash
python backend/main.py
```
2. להריץ את צד הלקוח (Frontend)
```bash
npm run dev
```
## הערות
- הפרויקט הוא Proof of concept ולא מוכן לשימוש חיצוני.
- הפרויקט למטרת למידה ולא למטרת שימוש, ולכן יכולים להיות באגים
