# Deploy to AWS EC2

This guide deploys the Flask app to an Ubuntu EC2 instance at `13.61.147.50`, serves it through Nginx and Gunicorn, and enables HTTPS for `pythonapp.creativeflow.name.ng`.

## 1. Prepare AWS and DNS

1. In the EC2 console, confirm the instance is running Ubuntu 22.04 or 24.04 and that you can connect with its SSH key. If `13.61.147.50` is not an Elastic IP, allocate and associate an Elastic IP first; otherwise, the address can change when the instance stops.
2. In the instance's security group, allow inbound:
   - SSH (TCP 22) only from your current public IP.
   - HTTP (TCP 80) from anywhere (`0.0.0.0/0` and `::/0`).
   - HTTPS (TCP 443) from anywhere (`0.0.0.0/0` and `::/0`).
3. At the DNS provider for `creativeflow.name.ng`, create an A record:
   - Name/host: `pythonapp`
   - Value/address: `13.61.147.50`
   - TTL: provider default

Wait until DNS resolves to `13.61.147.50` before requesting the HTTPS certificate. You can check from your computer with `nslookup pythonapp.creativeflow.name.ng`.

## 2. Connect and install server packages

From PowerShell on your computer, replace the key path with the location of your EC2 `.pem` key:

```powershell
ssh -i "C:\path\to\your-key.pem" ubuntu@13.61.147.50
```

Run the remaining commands in the SSH session on the Ubuntu instance:

```bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y git nginx python3-venv python3-pip certbot python3-certbot-nginx
```

## 3. Install the application

Clone the repository on the instance. Replace `<REPOSITORY_URL>` with this project's Git clone URL:

```bash
cd /home/ubuntu
git clone <REPOSITORY_URL> random-quotes-generator-python-app
cd /home/ubuntu/random-quotes-generator-python-app
python3 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt gunicorn
```

Check that Gunicorn can load the Flask application:

```bash
.venv/bin/gunicorn --workers 2 --bind 127.0.0.1:8000 app:app
```

After confirming it starts, press `Ctrl+C` to stop this temporary process.

## 4. Run Gunicorn with systemd

Create a service file:

```bash
sudo tee /etc/systemd/system/quotes-app.service > /dev/null <<'EOF'
[Unit]
Description=Random Quotes Flask application
After=network.target

[Service]
User=ubuntu
Group=www-data
WorkingDirectory=/home/ubuntu/random-quotes-generator-python-app
Environment="PATH=/home/ubuntu/random-quotes-generator-python-app/.venv/bin"
Environment="PYTHONUNBUFFERED=1"
ExecStart=/home/ubuntu/random-quotes-generator-python-app/.venv/bin/gunicorn --workers 2 --bind 127.0.0.1:8000 app:app
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF
```

Enable and start it:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now quotes-app
sudo systemctl status quotes-app --no-pager
```

The Gunicorn process listens only on localhost; public web traffic will enter through Nginx.

## 5. Configure Nginx

Create an Nginx site configuration:

```bash
sudo tee /etc/nginx/sites-available/quotes-app > /dev/null <<'EOF'
server {
    listen 80;
    listen [::]:80;
    server_name pythonapp.creativeflow.name.ng;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

sudo ln -s /etc/nginx/sites-available/quotes-app /etc/nginx/sites-enabled/quotes-app
sudo nginx -t
sudo systemctl reload nginx
```

If the default Nginx welcome page appears, disable the default site and reload Nginx:

```bash
sudo rm /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl reload nginx
```

## 6. Enable HTTPS

Once the DNS A record resolves correctly and port 80 is reachable, request and install a Let's Encrypt certificate:

```bash
sudo certbot --nginx -d pythonapp.creativeflow.name.ng
```

Follow the prompts and choose the option to redirect HTTP traffic to HTTPS. Verify automatic renewal:

```bash
sudo certbot renew --dry-run
```

Open [https://pythonapp.creativeflow.name.ng](https://pythonapp.creativeflow.name.ng) and refresh the page to check the quote generator.

## Updating the application

After pushing changes to the repository, connect to the instance and run:

```bash
cd /home/ubuntu/random-quotes-generator-python-app
git pull
.venv/bin/pip install -r requirements.txt gunicorn
sudo systemctl restart quotes-app
sudo systemctl status quotes-app --no-pager
```

For troubleshooting, inspect the service and Nginx logs:

```bash
sudo journalctl -u quotes-app -n 100 --no-pager
sudo tail -n 100 /var/log/nginx/error.log
```