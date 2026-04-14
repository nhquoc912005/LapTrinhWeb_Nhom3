# He Thong Quan Ly Van Ban

Du an Django cho nghiep vu "He thong Quan ly van ban va Dieu hanh".

## Chay local

1. Tao va kich hoat virtualenv.
2. Cai dependencies:
   `pip install -r requirements.txt`
3. Chay migration:
   `python manage.py migrate`
4. Kiem tra cau hinh:
   `python manage.py check`
5. Khoi dong server:
   `python manage.py runserver`

Database mac dinh la SQLite tai `db.sqlite3`. Thu muc upload runtime nam trong `media/` va da duoc dua vao `.gitignore`.
