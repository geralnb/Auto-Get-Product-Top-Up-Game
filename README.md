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