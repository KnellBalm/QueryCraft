# frontend/Dockerfile
FROM node:20-alpine as build

WORKDIR /app

COPY package*.json ./
RUN npm ci --legacy-peer-deps

COPY . .

# 빌드 인수 설정 (환경변수로 변환)
ARG VITE_API_URL
ARG VITE_MIXPANEL_TOKEN
ENV VITE_API_URL=$VITE_API_URL
ENV VITE_MIXPANEL_TOKEN=$VITE_MIXPANEL_TOKEN

RUN npm run build

# Production - Cloud Run용 Nginx 설정
FROM nginx:alpine

# 기본 nginx 설정 제거 후 커스텀 설정 사용
RUN rm /etc/nginx/conf.d/default.conf

# 빌드된 파일 복사
COPY --from=build /app/dist /usr/share/nginx/html

# Cloud Run용 nginx 설정 (PORT 환경변수 사용)
COPY nginx.conf /etc/nginx/nginx.conf

# Cloud Run은 PORT 환경변수를 제공하므로 8080으로 설정
EXPOSE 8080

# nginx foreground 실행
CMD ["nginx", "-g", "daemon off;"]
