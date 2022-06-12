# dmhunter
Hunt for 弹幕（目前只接入了微信公众号）

Requires python>=3.6

Django
```
venv/bin/python3 manage.py runserver
```

Redis
```
docker run -p 127.0.0.1:16379:6379 -v /srv/redis_data_production:/data -d --restart always --name redis_production redis
```

cqhttp
```
docker run -tid --rm --name cqhttp \
    -v $(pwd)/coolq:/home/user/coolq \
    -p 9000:9000 \
    -e COOLQ_ACCOUNT=10000 \
    -e CQHTTP_POST_URL=https://dmhunter.tsing.net/dmhunter/cqhttpcallback \
    -e CQHTTP_SECRET=CQHTTP_SECRET \
    -e VNC_PASSWD=PASSWORD \
    -e FORCE_ENV=true \
    richardchien/cqhttp:latest
```
