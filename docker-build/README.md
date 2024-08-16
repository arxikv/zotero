# How to build

1. Get back into the repo's root directory.
2. Get Docker Engine v23.0+ installed.
3. Download [this](https://nextcloud.ispras.ru/index.php/s/Ej8ayHrGRqAxGyP) file to
   `app/xulrunner` directory.
4. Build:

```bash
docker build \
    -f docker-build/Dockerfile \
    --target=packages --output=packages \
    --build-arg MAINTAINER="Konstantin Arkhipenko <arkhipenko@ispras.ru>" \
    .
```
