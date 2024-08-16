FROM sitespeedio/node:ubuntu-20.04-nodejs-18.12.0 AS builder

ARG MAINTAINER

RUN apt-get update && \
    apt-get -y dist-upgrade && \
    apt-get -y install binutils bzip2 curl git git-lfs p7zip-full python3 rsync unzip \
        vim-common xz-utils zip

COPY . /zotero-client
WORKDIR /zotero-client

RUN cp docker-build/config.js resource/config.js && \
    npm install && \
    npm run build

RUN git lfs pull

# Build Linux x64 client
RUN ./app/scripts/dir_build -p l

# Create .deb package
RUN cd docker-build/deb && \
    python3 build.py \
        /zotero-client/app/staging/Zotero_linux-x86_64 \
        /packages \
        "$MAINTAINER"

# Build and archive Windows x64 and arm64 clients
RUN ./app/scripts/dir_build -p w && \
    cd app/staging && \
    zip -rqX /packages/Zotero7_win-x64.zip Zotero_win-x64 && \
    zip -rqX /packages/Zotero7_win-arm64.zip Zotero_win-arm64

# Build and archive macOS client
RUN ./app/scripts/dir_build -p m && \
    cd app/staging && \
    zip -rqX /packages/Zotero7_mac.zip Zotero.app

FROM scratch AS packages

COPY --from=builder /packages/ /
