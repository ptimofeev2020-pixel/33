import re

from rest_framework.serializers import ValidationError

URL_PATTERN = re.compile(r'(?:https?://|www\.)\S+', re.IGNORECASE)
ALLOWED_DOMAINS = ('youtube.com', 'www.youtube.com', 'm.youtube.com', 'youtu.be')


class YoutubeLinkValidator:
    def __init__(self, field):
        self.field = field

    def __call__(self, attrs):
        value = attrs.get(self.field)
        if not value:
            return
        for url in URL_PATTERN.findall(str(value)):
            domain = re.sub(r'^(?:https?://)', '', url, flags=re.IGNORECASE).split('/')[0].lower()
            if domain not in ALLOWED_DOMAINS:
                raise ValidationError(
                    {self.field: 'Разрешены только ссылки на youtube.com. Ссылки на сторонние ресурсы запрещены.'}
                )
