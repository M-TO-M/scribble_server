from enum import Enum


class ChoicesEnum(Enum):
    @classmethod
    def choices(cls):
        return tuple((item.value, item.value) for i, item in enumerate(cls))

    @classmethod
    def choices_list(cls):
        return list(item.value for i, item in enumerate(cls))


class CategoryChoices(ChoicesEnum):
    LITERARY_FICTION = '소설(국내, 외국)'
    ECONOMICS_MANAGEMENT = '경제/경영'
    SELF_DEVELOPMENT = '자기계발'
    HISTORY = '역사'
    RELIGION_SPIRITUALITY = '종교'
    POLITICS_SOCIETY = '정치/사회'
    ART_CULTURE = '예술/문화'
    COMPUTER_TECHNOLOGY_ENGINEERING = '컴퓨터/IT/기술공학'
    SCIENCE = '과학'


class DomainChoices(ChoicesEnum):
    NAVER = "naver.com"
    GMAIL = "gmail.com"
    DAUM = "daum.net"
    HANMAIL = "hanmail.net"
    NATE = "nate.com"
    HOTMAIL = "hotmail.com"
    ICLOUD = "icloud.com"
