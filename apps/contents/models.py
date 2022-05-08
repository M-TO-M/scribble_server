from django.db import models

from core.fields import ISBNField
from core.models import TimeStampModel, Default
from apps.users.models import User


DEFAULT_MODEL_PK = Default(
    user=0,
    book_object=1,
    note=2,
    page=3,
    page_comment=4
)


class BookObject(TimeStampModel):
    isbn = ISBNField(normalize_isbn=True, unique=True)
    title = models.CharField(
        max_length=150,
        verbose_name='제목'
    )
    author = models.CharField(
        max_length=150,
        verbose_name='작가'
    )
    publisher = models.CharField(
        max_length=150,
        verbose_name='출판사'
    )
    category = models.JSONField(
        default=dict
    )
    thumbnail = models.URLField(
        blank=True,
        null=False,
        verbose_name='도서 썸네일'
    )

    class Meta:
        db_table = 'book'
        verbose_name = '도서'
        verbose_name_plural = verbose_name
        ordering = ['created_at']


class Note(TimeStampModel):
    user = models.ForeignKey(
        User,
        on_delete=models.SET_DEFAULT,
        default=DEFAULT_MODEL_PK.user,
        related_name='note',
        verbose_name='작성자'
    )
    book = models.ForeignKey(
        BookObject,
        on_delete=models.SET_DEFAULT,
        default=DEFAULT_MODEL_PK.book_object,
        related_name='note',
        verbose_name='도서'
    )
    hit = models.PositiveSmallIntegerField(
        default=0,
        verbose_name='조회수'
    )

    class Meta:
        db_table = 'note'
        verbose_name = '필사 노트'
        verbose_name_plural = verbose_name


class NoteLikesRelation(TimeStampModel):
    like_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='note_likes_relation',
        verbose_name='사용자'
    )
    note = models.ForeignKey(
        Note,
        on_delete=models.CASCADE,
        related_name='note_likes_relation',
        verbose_name='노트'
    )

    class Meta:
        db_table = 'note_likes_relation'
        verbose_name = '노트_좋아요'
        verbose_name_plural = verbose_name


class Page(TimeStampModel):
    note = models.ForeignKey(
        Note,
        on_delete=models.SET_DEFAULT,
        default=DEFAULT_MODEL_PK.note,
        related_name='page',
        verbose_name='노트'
    )
    note_index = models.PositiveSmallIntegerField(
        default=0,
        verbose_name='노트 인덱스'
    )
    transcript = models.URLField(
        blank=False,
        null=False,
        verbose_name='필사 이미지'
    )
    phrase = models.TextField(
        blank=True,
        null=True,
        verbose_name='필사 구절'
    )
    hit = models.PositiveSmallIntegerField(
        default=0,
        verbose_name='조회수'
    )

    class Meta:
        db_table = 'page'
        verbose_name = '필사 페이지'
        verbose_name_plural = verbose_name
        ordering = ['created_at']


class PageLikesRelation(TimeStampModel):
    like_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='page_likes_relation',
        verbose_name='사용자'
    )
    page = models.ForeignKey(
        Page,
        on_delete=models.CASCADE,
        related_name='page_likes_relation',
        verbose_name='페이지'
    )

    class Meta:
        db_table = 'page_likes_relation'
        verbose_name = '페이지_좋아요'
        verbose_name_plural = verbose_name
        ordering = ['created_at']


class PageComment(TimeStampModel):
    page = models.ForeignKey(
        Page,
        on_delete=models.SET_DEFAULT,
        default=DEFAULT_MODEL_PK.page,
        related_name='page_comment',
        verbose_name='페이지'
    )
    depth = models.PositiveSmallIntegerField(
        default=0,
        verbose_name='댓글 depth'
    )
    parent = models.PositiveSmallIntegerField(
        default=0,
        verbose_name='부모 댓글 idx'
    )
    content = models.TextField(
        verbose_name='내용'
    )

    class Meta:
        db_table = 'page_comment'
        verbose_name = '페이지 댓글'
        verbose_name_plural = verbose_name
