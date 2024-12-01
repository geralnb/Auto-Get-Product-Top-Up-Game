## check_price.py 
menjalankan flask secara otomatis sebagai berikut:
1. buat 
```sh
sudo nano /etc/systemd/system/flask_app.service
```
lalu isi dengan
```sh
[Unit]
Description=Flask Application
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/python
ExecStart=/usr/bin/python3 /home/ubuntu/python/check_price.py flask
Restart=always

[Install]
WantedBy=multi-user.target
```
2. Reload systemd 
```sh
sudo systemctl daemon-reload
```
3. Start Flask Service 
```sh
sudo systemctl start flask_app
```
4. Periksa Status
```sh
sudo systemctl status flask_app
```
## Untuk Menjalankan curl otomatis
1. Buka Crontab
``` sh
crontab -e
```
2. Tambahkan Cron Job
``` sh
*/15 * * * * curl "http://127.0.0.1:5000/export_xlsx?codes=XXXX" >> /home/ubuntu/cron_curl.log 2>&1
```
Penjelasan:
- */15 * * * *: Menjalankan perintah setiap 15 menit.
- curl "http://127.0.0.1:5000/... : Perintah untuk menjalankan curl ke endpoint Flask.
-  /home/ubuntu/cron_curl.log: Output akan disimpan ke file log /home/ubuntu/cron_curl.log.
- 2>&1: Menangkap error dan menyimpannya ke log yang sama.