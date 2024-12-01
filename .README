Untuk check_price.py menjalankan flask secara otomatis sebagai berikut:
1. "sudo nano /etc/systemd/system/flask_app.service" lalu isi dengan
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
2. Reload systemd "sudo systemctl daemon-reload"
3. Start Flask Service "sudo systemctl start flask_app"
4. Periksa Status "sudo systemctl status flask_app"