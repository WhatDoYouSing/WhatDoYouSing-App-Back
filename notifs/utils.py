import requests, itertools

EXPO_PUSH_URL = "https://exp.host/--/api/v2/push/send"


def chunks(iterable, size=100):
    it = iter(iterable)
    while batch := list(itertools.islice(it, size)):
        yield batch


def send_expo_push(tokens, title, body, data=None):
    """
    tokens : ExponentPushToken[...] 리스트
    data   : {"notif_id": 123} 처럼 딥링크용 JSON
    """
    messages = [
        {
            "to": t,
            "title": title,
            "body": body,
            "sound": "default",
            "data": data or {},
        }
        for t in tokens
    ]

    for batch in chunks(messages, 100):
        requests.post(EXPO_PUSH_URL, json=batch, timeout=10)
