FROM lend-backend:before-public-links-20261028
COPY backend/app /app/backend/app
LABEL org.lend.release="20261028-public-links"
