from django.db import models
from django.db.models import UniqueConstraint

from api.contents.fields import ISBNField
from apps.models import TimeStampModel
from apps.users.models import User


USER__DEFAULT_PK = 0
BOOK_OBJECT__DEFAULT_PK = 1
NOTE__DEFAULT_PK = 2
PAGE__DEFAULT_PK = 3
PAGE_COMMENT__DEFAULT_PK = 4


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
        default=USER__DEFAULT_PK,
        related_name='note',
        verbose_name='작성자'
    )
    book = models.ForeignKey(
        BookObject,
        on_delete=models.SET_DEFAULT,
        default=BOOK_OBJECT__DEFAULT_PK,
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
        ordering = ['created_at']
        # TASK 4: 동일한 user, book에 대하여 여러 개의 note object가 생성되는 버그 수정 (UniqueConstraint 지정)
        constraints = [
            UniqueConstraint(
                fields=['user', 'book'],
                name='user_book_unique_together'
            )
        ]

    def update_note_hit(self):
        self.hit += 1
        self.save()


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
        default=NOTE__DEFAULT_PK,
        related_name='page',
        verbose_name='노트'
    )
    note_index = models.PositiveSmallIntegerField(
        default=0,
        verbose_name='노트 인덱스'
    )
    # TASK 2: 책 등록 이미지 url max_length 수정
    transcript = models.URLField(
        blank=False,
        null=False,
        max_length=500,
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
    book_page = models.PositiveSmallIntegerField(
        default=0,
        verbose_name='책페이지',
        blank=True
    )

    class Meta:
        db_table = 'page'
        verbose_name = '필사 페이지'
        verbose_name_plural = verbose_name
        ordering = ['created_at']

    def update_page_hit(self):
        self.hit += 1
        self.save()

    def save_new_note_index(self):
        index_list = Page.objects.filter(note_id=self.note.id).values_list('note_index', flat=True)
        value = max(index_list) + 1 if index_list else 0
        self.note_index = value
        self.save()


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
    comment_user = models.ForeignKey(
        User,
        on_delete=models.SET_DEFAULT,
        default=PAGE_COMMENT__DEFAULT_PK,
        related_name='page_comment',
        verbose_name='작성자'
    )

    page = models.ForeignKey(
        Page,
        on_delete=models.SET_DEFAULT,
        default=PAGE__DEFAULT_PK,
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
