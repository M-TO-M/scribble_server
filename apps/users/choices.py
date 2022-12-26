from enum import Enum


class ChoicesEnum(Enum):
    @classmethod
    def choices(cls):
        return tuple((item.value, item.value) for item in cls)

    @classmethod
    def choices_list(cls):
        return list(item.value for item in cls)


class SocialAccountTypeEnum(ChoicesEnum):
    DEFAULT = 'default'
    KAKAO = 'kakao'
