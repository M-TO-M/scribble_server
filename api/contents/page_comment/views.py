import json

from django.utils.translation import gettext_lazy as _

from rest_framework import generics, mixins, status
from rest_framework.exceptions import AuthenticationFailed, ValidationError
from rest_framework.response import Response

from api.contents.page_comment.serializers import PageCommentSerializer, PageCommentCreateUpdateSerializer
from apps.contents.models import PageComment
from core.exceptions import PageCommentNotFound


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

    def get(self, request, *args, **kwargs):
        page_comment = self.get_page_comment_object()
        page_comment_data = self.serializer_class(instance=page_comment).data
        response = {"page_comment": page_comment_data}

        return Response(response, status.HTTP_200_OK)

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

    def delete(self, request, *args, **kwargs):
        page_comment = self.get_page_comment_object()
        self.authentication(page_comment)

        self.perform_destroy(page_comment)
        return Response(None, status=status.HTTP_204_NO_CONTENT)
