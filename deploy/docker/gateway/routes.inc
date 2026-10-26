# Routes of the Lend gateway, shared by http.conf, https.conf and proxy.conf.
# The browser sees one address: /api/v1/ goes to the backend, everything else to Next.js.
# Same origin for both is what makes the HttpOnly session cookie work.
# The including server sets $lend_proto: the scheme the visitor used (http or https).

client_max_body_size 60m;

gzip on;
gzip_types text/plain text/css application/javascript application/json image/svg+xml;
gzip_min_length 1024;

add_header X-Content-Type-Options nosniff always;
add_header Referrer-Policy same-origin always;

# Docker's DNS: a container that restarts gets a new address, so names are resolved per request.
resolver 127.0.0.11 valid=10s ipv6=off;
set $lend_backend http://backend:8001;
set $lend_frontend http://frontend:3000;

proxy_http_version 1.1;
proxy_set_header Host $host;
proxy_set_header X-Real-IP $remote_addr;
proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
proxy_set_header X-Forwarded-Proto $lend_proto;
proxy_set_header X-Forwarded-Host $http_host;

location = /health {
    proxy_pass $lend_backend;
}

location /api/v1/ {
    # Building a landing from large files can take minutes.
    proxy_read_timeout 300s;
    proxy_send_timeout 300s;
    proxy_pass $lend_backend;
}

location / {
    proxy_read_timeout 120s;
    proxy_pass $lend_frontend;
}
