# Stage 0, "build-stage", based on Node.js, to build and compile the frontend
FROM node:24 AS build-stage

WORKDIR /app

COPY package*.json /app/

# npm ci (S6-H4): enforce package-lock.json exactly; `npm install` could
# silently re-resolve — the same defect class as the backend's unlocked sync.
RUN npm ci

COPY ./ /app/

ARG VITE_API_URL=${VITE_API_URL}

RUN npm run build


# Stage 1, based on Nginx, to have only the compiled app, ready for production with Nginx
# Pinned tag (S6-H4): the floating `nginx:1` major could jump versions between builds.
FROM nginx:1.27-alpine

COPY --from=build-stage /app/dist/ /usr/share/nginx/html

COPY ./nginx.conf /etc/nginx/conf.d/default.conf
COPY ./nginx-backend-not-found.conf /etc/nginx/extra-conf.d/backend-not-found.conf
