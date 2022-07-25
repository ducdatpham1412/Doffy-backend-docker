FROM python:3.9 as app
WORKDIR /usr/src
COPY requirements.txt requirements.txt
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
COPY app app


FROM node:16-alpine as chat
WORKDIR /usr/src
COPY package.json package.json
COPY tsconfig.json tsconfig.json
COPY chat chat
RUN npm install -g typescript
RUN yarn