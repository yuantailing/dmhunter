# dmhunter
Hunt for 弹幕（目前只接入了微信公众号）

Requires python>=3.6

Django
```
venv/bin/python3 manage.py runserver
```

Redis
```
docker run -p 127.0.0.1:16379:6379 -v /srv/redis_data_production:/data -d --name redis_production redis
```
