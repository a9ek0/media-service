import markdown

from django.http import HttpResponse
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample
from drf_spectacular.types import OpenApiTypes
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.views import APIView
from django.utils.translation import gettext_lazy as _

from news.models import Category, Post, Video
from news.serializers.apiv2_serializers import PostSerializer, NewsItemSerializer, CategorySerializer, NewsFeedQueryParamsSerializer, \
    NewsFeedExcludedRequestSerializer


class NewsFeedPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'pageSize'
    page_query_param = 'pageNumber'
    max_page_size = 100


class NewsFeedAPIView(APIView):
    serializer_class = NewsItemSerializer

    @extend_schema(
        parameters=[NewsFeedQueryParamsSerializer],
        responses={ 200: PostSerializer(many=True), },
        description="Получить ленту новостей и видео.",
        summary="Лента новостей",
        tags=["Новости"]
    )
    def get(self, request):
        param_serializer = NewsFeedQueryParamsSerializer(data=request.GET)
        param_serializer.is_valid(raise_exception=True)
        params = param_serializer.validated_data

        page_size = params['pageSize']
        page_number = params['pageNumber']
        category_id = params.get('categoryId')
        all_news = params['allNews']

        articles = Post.objects.filter(status='published').select_related('category', 'author')
        videos = Video.objects.filter(status='published').select_related('category', 'author')

        if category_id:
            try:
                category_id_int = int(category_id)
                articles = articles.filter(category_id=category_id_int)
                videos = videos.filter(category_id=category_id_int)
            except ValueError:
                pass

        articles_list = list(articles)
        videos_list = list(videos)

        all_content = sorted(
            articles_list + videos_list,
            key=lambda x: x.published_at if x.published_at else x.created_at,
            reverse=True
        )

        if all_news:
            serializer = NewsItemSerializer(all_content, many=True)
            return Response({
                'data': serializer.data,
                'meta': {
                    'totalCount': len(all_content)
                }
            })

        paginator = NewsFeedPagination()
        paginator.page_size = page_size

        start_index = (page_number - 1) * page_size
        end_index = start_index + page_size
        paginated_content = all_content[start_index:end_index]

        serializer = NewsItemSerializer(paginated_content, many=True)

        return Response({
            'data': serializer.data,
            'meta': {
                'totalCount': len(all_content),
            }
        })

    @extend_schema(
        request=NewsFeedExcludedRequestSerializer,
        responses={ 200: PostSerializer(many=True), },
        description="Получить полную ленту новостей и видео, исключая элементы с указанными ID.",
        summary="Лента новостей с исключением по ID",
        tags=["Новости"]
    )
    def post(self, request):
        input_serializer = NewsFeedExcludedRequestSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)
        excluded_ids = input_serializer.validated_data['excluded']

        articles = Post.objects.filter(status='published').exclude(id__in=excluded_ids)
        videos = Video.objects.filter(status='published').exclude(id__in=excluded_ids)

        articles_list = list(articles)
        videos_list = list(videos)

        all_content = sorted(
            articles_list + videos_list,
            key=lambda x: x.published_at if x.published_at else x.created_at,
            reverse=True
        )

        serializer = NewsItemSerializer(all_content, many=True)
        return Response({
            'data': serializer.data,
            'meta': {
                'totalCount': len(all_content)
            }
        })


class NewsCategoriesAPIView(APIView):
    serializer_class = CategorySerializer
    queryset = Category.objects.all()

    @extend_schema(
        responses={200: CategorySerializer(many=True)},
        description="Получить дерево категорий новостей и видео.",
        summary="Список категорий",
        tags=["Новости"]
    )
    def get(self, request):
        categories = Category.objects.all().prefetch_related('children')
        serializer = CategorySerializer(categories, many=True)
        return Response({
            'data': serializer.data
        })


@extend_schema(
    responses={
        200: OpenApiResponse(
            description="HTML-представление указанной новости",
            response=OpenApiTypes.STR,
            examples=[
                OpenApiExample(
                    'Пример HTML',
                    value='<h1>Заголовок</h1><p>Текст новости...</p>',
                    media_type='text/html'
                )
            ]
        ),
        404: OpenApiResponse(
            description="Новость/видео не найдено",
            response=OpenApiTypes.OBJECT,
            examples=[
                OpenApiExample(
                    'Пример ошибки',
                    value={
                        'errors': [{
                            'code': 'string',
                            'title': 'string',
                            'details': 'string'
                        }]
                    }
                )
            ]
        )
    },
    description="Возвращает HTML-представление конкретной новости или видео.",
    summary="HTML-представление указанной новости",
    tags=["Новости"],
    operation_id="news_detail_html"
)
@api_view(['GET'])
def news_detail_html(request, newsItemId):
    try:
        content_item = Post.objects.get(id=newsItemId, status='published')
        if content_item.body:
            html_content = markdown.markdown(content_item.body)
        else:
            html_content = None
    except Post.DoesNotExist:
        return Response({
            'errors': [{
                'code': 'not_found',
                'title': 'Object not found',
                'details': f'Article with ID {newsItemId} does not exist'
            }]
        }, status=status.HTTP_404_NOT_FOUND)

    return HttpResponse(html_content or "<p>" + _("Контент отсутствует") + "</p>", content_type='text/html')
