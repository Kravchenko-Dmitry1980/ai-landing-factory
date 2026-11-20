FROM lend-frontend:before-public-links-20261028
WORKDIR /app
COPY frontend/ ./
ENV NEXT_PUBLIC_API_URL=/api/v1 INTERNAL_API_URL=http://backend:8001/api/v1 API_PROXY_TARGET="" NEXT_TELEMETRY_DISABLED=1 SESSION_COOKIE_NAME=lend_session
RUN node -e "require('fs').rmSync('/app/.next',{recursive:true,force:true})" && npm run build
LABEL org.lend.release="20261028-public-links"
