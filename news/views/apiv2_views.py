import markdown

from django.http import HttpResponse, HttpResponseNotFound
from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample
from drf_spectacular.types import OpenApiTypes

from news.models import Category, ContentItem
from news.serializers.apiv2_serializers import (
    CategorySerializer,
    ContentItemSerializer,
    NewsFeedQueryParamsSerializer,
    NewsFeedExcludedRequestSerializer,
)
from news.utils import get_category_and_descendants_ids


class NewsFeedAPIView(APIView):
    serializer_class = ContentItemSerializer

    @extend_schema(
        parameters=[NewsFeedQueryParamsSerializer],
        responses={200: ContentItemSerializer(many=True)},
        description="Получить ленту новостей и видео.",
        summary="Лента новостей",
        tags=["Новости"],
    )
    def get(self, request):
        params_serializer = NewsFeedQueryParamsSerializer(data=request.GET)
        params_serializer.is_valid(raise_exception=True)
        params = params_serializer.validated_data

        page_size = params["pageSize"]
        page_number = params["pageNumber"]
        category_id = params.get("categoryId")
        all_news = params["allNews"]

        qs = (
            ContentItem.objects.filter(status=ContentItem.Status.PUBLISHED)
            .only("id", "title", "lead", "published_at", "created_at", "title_picture", "category_id", "content_type")
            .select_related("category")
            .order_by("-published_at", "-updated_at")
        )

        total_count = qs.count()

        if not all_news and category_id is not None:
            category_ids = get_category_and_descendants_ids(category_id)
            if category_ids:
                qs = qs.filter(category_id__in=category_ids)
            else:
                qs = qs.none()

        if not all_news:
            offset = (page_number - 1) * page_size
            qs = qs[offset : offset + page_size]

        serializer = ContentItemSerializer(qs, many=True)
        return Response({"data": serializer.data, "meta": {"totalCount": total_count}})

    @extend_schema(
        request=NewsFeedExcludedRequestSerializer,
        responses={200: ContentItemSerializer(many=True)},
        description="Получить ленту новостей и видео, исключая элементы с указанными ID.",
        summary="Лента новостей с исключением по ID",
        tags=["Новости"],
    )
    def post(self, request):
        input_serializer = NewsFeedExcludedRequestSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)
        excluded_ids = input_serializer.validated_data.get("excluded", [])

        qs = (
            ContentItem.objects.filter(status=ContentItem.Status.PUBLISHED)
            .exclude(id__in=excluded_ids)
            .only(
                "id",
                "title",
                "lead",
                "published_at",
                "created_at",
                "title_picture",
                "category_id",
            )
            .select_related("category")
            .prefetch_related("category__category_set")
            .order_by("-published_at", "-updated_at")
        )

        serializer = ContentItemSerializer(qs, many=True)
        return Response({"data": serializer.data, "meta": {"totalCount": qs.count()}})


class NewsCategoriesAPIView(APIView):
    serializer_class = CategorySerializer
    queryset = Category.objects.all()

    @extend_schema(
        responses={200: CategorySerializer(many=True)},
        description="Получить дерево категорий новостей и видео.",
        summary="Список категорий",
        tags=["Новости"],
    )
    def get(self, request):
        categories = Category.objects.filter(parent__isnull=True).prefetch_related(
            "category_set", "category_set__category_set", "category_set__category_set__category_set"
        )
        serializer = CategorySerializer(categories, many=True)
        return Response({"data": serializer.data})


@extend_schema(
    responses={
        200: OpenApiResponse(
            description="HTML-представление указанной новости или видео",
            response=OpenApiTypes.STR,
            examples=[
                OpenApiExample(
                    "Пример HTML", value="<h1>Заголовок</h1><p>Текст контента...</p>", media_type="text/html"
                )
            ],
        ),
        404: OpenApiResponse(
            description="Контент не найден",
            response=OpenApiTypes.OBJECT,
            examples=[
                OpenApiExample(
                    "Пример ошибки", value={"errors": [{"code": "not_found", "details": "Content not found"}]}
                )
            ],
        ),
    },
    description="Возвращает HTML-представление контентного элемента (новости или видео).",
    summary="HTML-представление контента",
    tags=["Новости"],
)
@api_view(["GET"])
def news_detail_html(request, newsItemId):
    try:
        content_item = ContentItem.objects.get(id=newsItemId, status=ContentItem.Status.PUBLISHED)
    except ContentItem.DoesNotExist:
        # Json в соответствии со спецификацией
        return Response(
            {"errors": [{"code": "not_found", "title": "Not Found", "details": "Content not found"}]},
            status=status.HTTP_404_NOT_FOUND,
            content_type="application/json",
        )

    html_content = (
        markdown.markdown(content_item.body or "") if content_item.body else "<p>" + _("Контент отсутствует") + "</p>"
    )

    return HttpResponse(html_content, content_type="text/html; charset=utf-8")
