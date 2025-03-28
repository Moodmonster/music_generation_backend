from typing import Literal

class Content:
    def __init__(self, title: str, description: str, author: str, userId: int, contentType: Literal["novel", "webtoon"]):
        self.title = title
        self.description = description
        self.author = author
        self.userId = userId
        self.contentType = contentType
        
        self.contentCode = 0  # todo: random 생성 기능
        self.clickCount = 0
        self.thumbnailUrl = "" # todo: ai 이미지 생성 기능능

    def getJson(self):
        return {
            "code": self.contentCode,
            "title": self.title,
            "desc": self.description,
            "author": self.author,
            "userId": self.userId,
            "contentType": self.contentType,
            "clickCount": self.clickCount,
            "thumbnailUrl": self.thumbnailUrl
        }

class Episode:
    def __init__(self, contentCode, episodeTitle, uploadDate, thumbnailUrl):
        self.contentCode = contentCode
        self.episodeTitle = episodeTitle
        self.uploadDate = uploadDate
        self.thumbnailUrl = thumbnailUrl
        
        self.episodeCode = 0 # index 처럼 사용
        self.