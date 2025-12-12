# Nginx Configuration on a Linux Server

Use Nginx as a reverse proxy to serve the "investorly" application running in Docker containers.

## 1. Create a new file investorly in the /etc/nginx/sites-available directory:
```bash
$ sudo vim /etc/nginx/sites-available/investorly
```

## 2. Add the following configuration:

```conf
# /etc/nginx/sites-available/investorly

# Define a server block.
server {
    # Listen on port 80 (default HTTP port).
    listen 80;

    # Define the domain name(s).
    server_name investorly.qingquanli.com;

    # Define the location for the root URL.
    location / {
        # 8030 is the frontend service port defined in the docker-compose.yml file.
        proxy_pass http://localhost:8030;

        # WebSocket support (critical for Streamlit)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # Standard headers
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Optional: avoid timeouts on long WS connections
        proxy_read_timeout 86400;
    }
}
```


## 3. Create a symbolic link to the file in the /etc/nginx/sites-enabled directory:
```bash
$ sudo ln -s /etc/nginx/sites-available/investorly /etc/nginx/sites-enabled/
```

## 4. Test the Nginx configuration:
```bash
$ sudo nginx -t
```


## 5. Reload Nginx to apply the changes:
```bash
$ sudo systemctl reload nginx
```


## 6. Optional: Configure HTTPS

- Use Cloudflare DNS proxy to enable HTTPS (it can also enable to hide the IP address of the server)
- Or: Configure Let's Encrypt (certbot) in Nginx to enable HTTPS
