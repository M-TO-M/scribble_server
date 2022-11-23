import json

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from django.utils.translation import gettext_lazy as _

from rest_framework import generics, mixins, status
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.response import Response

from api.contents.page_comment.serializers import *
from apps.contents.models import PageComment
from api.contents.exceptions import PageCommentNotFound
from utils.swagger import swagger_response, swagger_schema_with_description, swagger_schema_with_properties, \
    PageCommentFailCaseCollection as page_comment_fail_case, UserFailCaseCollection as user_fail_case, \
    page_comment_response_example


class PageCommentView(generics.GenericAPIView,
                      mixins.RetrieveModelMixin,
                      mixins.CreateModelMixin,
                      mixins.UpdateModelMixin,
                      mixins.DestroyModelMixin):
    queryset = PageComment.objects.all().select_related('page__note__user')
    serializer_class = PageCommentSerializer

    def get_page_comment_object(self) -> PageComment:
        try:
            page_comment = self.get_object()
        except Exception:
            raise PageCommentNotFound()

        return page_comment

    def authentication(self, obj: PageComment) -> bool:
        if self.request.user.id != obj.comment_user.id:
            raise AuthenticationFailed(detail=_("unauthorized_user"))
        return True

    @swagger_auto_schema(
        operation_id='page_comment_detail',
        operation_description='페이지 코멘트를 조회합니다.',
        responses={
            200: swagger_response(
                description='PAGE_COMMENT_200_DETAIL',
                schema=PageCommentSchemaSerializer,
                examples=page_comment_response_example
            ),
            404: page_comment_fail_case.PAGE_COMMENT_404_DOES_NOT_EXIST.as_md()
        }
    )
    def get(self, request, *args, **kwargs):
        page_comment = self.get_page_comment_object()
        page_comment_data = self.serializer_class(instance=page_comment).data
        response = {"page_comment": page_comment_data}

        return Response(response, status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_id='page_comment_new',
        operation_description='페이지 코멘트를 등록합니다.',
        request_body=swagger_schema_with_properties(
            openapi.TYPE_OBJECT,
            {
                'page': swagger_schema_with_description(openapi.TYPE_INTEGER, '페이지 id'),
                'parent': swagger_schema_with_description(openapi.TYPE_INTEGER, '상위 댓글 id (default=0)'),
                'content': swagger_schema_with_description(openapi.TYPE_STRING, '댓글 내용'),
            }
        ),
        responses={
            201: swagger_response(
                description='PAGE_COMMENT_201_NEW',
                schema=PageCommentSchemaSerializer,
                examples=page_comment_response_example
            ),
            400:
                page_comment_fail_case.PAGE_COMMENT_400_NO_PAGE_PK_IN_REQUEST_BODY.as_md() +
                page_comment_fail_case.PAGE_COMMENT_400_INVALID_PARENT_COMMENT.as_md(),
            404:
                page_comment_fail_case.PAGE_COMMENT_404_DOES_NOT_EXIST.as_md() +
                page_comment_fail_case.PAGE_COMMENT_404_PARENT_COMMENT_DOES_NOT_EXIST.as_md()
        }
    )
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
        except Exception:
            raise ValidationError(detail=_("no_data_in_req_body"))

        if "page" not in data:
            raise ValidationError(detail=_("no_page_pk_in_body"))

        page_comment_data = {
            "comment_user": self.request.user,
            "page": data["page"],
            "parent": data.pop('parent', 0),
            "content": data["content"]
        }

        page_comment_create_serializer = PageCommentCreateUpdateSerializer()
        page_comment = page_comment_create_serializer.create(validated_data=page_comment_data)

        response = {
            "page_comment": self.serializer_class(instance=page_comment).data
        }
        return Response(response, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(
        operation_id='page_comment_edit',
        operation_description='페이지 코멘트를 수정합니다.',
        responses={
            201: swagger_response(
                description='PAGE_COMMENT_201_EDIT',
                schema=PageCommentSchemaSerializer,
                examples=page_comment_response_example
            ),
            400: page_comment_fail_case.PAGE_COMMENT_400_EDIT_VALIDATION_ERROR.as_md(),
            401: user_fail_case.USER_401_UNAUTHORIZED.as_md(),
            404: page_comment_fail_case.PAGE_COMMENT_404_DOES_NOT_EXIST.as_md()
        }
    )
    def patch(self, request, *args, **kwargs):
        page_comment = self.get_page_comment_object()
        self.authentication(page_comment)

        data = json.loads(request.body)
        page_comment_serializer = self.serializer_class(data=data)
        page_comment_serializer.is_valid(raise_exception=True)
        update_page_comment = page_comment_serializer.update(instance=page_comment, validated_data=data)

        response = {
            "page_comment": self.serializer_class(instance=update_page_comment).data
        }
        return Response(response, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(
        operation_id='page_comment_delete',
        operation_description='페이지 코멘트를 삭제합니다.',
        responses={
            204: swagger_response(description='PAGE_COMMENT_204_DELETE'),
            401: user_fail_case.USER_401_UNAUTHORIZED.as_md(),
            404: page_comment_fail_case.PAGE_COMMENT_404_DOES_NOT_EXIST.as_md()
        }
    )
    def delete(self, request, *args, **kwargs):
        page_comment = self.get_page_comment_object()
        self.authentication(page_comment)

        self.perform_destroy(page_comment)
        return Response(None, status=status.HTTP_204_NO_CONTENT)
