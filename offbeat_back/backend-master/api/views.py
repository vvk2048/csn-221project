from datetime import datetime, timedelta
from django.http import Http404
from django.shortcuts import render, get_object_or_404
from rest_framework import response, views, generics, viewsets, permissions, decorators
from django.contrib.postgres.search import SearchVector
from django.utils import timezone

from django.db.models import F, Q
from django.db.models.functions import Extract
from django.core.paginator import Paginator

from .models import *
from .serializers import *
from .pagination import *

class CategoryView(generics.ListAPIView):
    queryset = Category.objects.all().order_by('name')
    serializer_class = CategorySerializer


class TagView(generics.ListAPIView):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class TopicView(generics.ListAPIView):
    queryset = Topic.objects.all().order_by('priority')
    serializer_class = TopicSerializer


class QuoteView(generics.ListAPIView):
    queryset = Quote.objects.filter(visibility = True)
    serializer_class = QuoteSerializer


class MyTagViewSet(viewsets.ModelViewSet):
    queryset = MyTag.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = MyTagSerializer

    def get_queryset(self):
        return MyTag.objects.filter(user = self.request.user)

    def perform_create(self, serializer):
        serializer.save(user = self.request.user)
        return super(MyTagViewSet, self).perform_create(serializer)

    def perform_update(self, serializer):
        serializer.save(user = self.request.user)
        return super(MyTagViewSet, self).perform_update(serializer)


class MyCategoryViewSet(viewsets.ModelViewSet):
    queryset = MyCategory.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = MyCategorySerializer

    def get_queryset(self):
        return MyCategory.objects.filter(user = self.request.user)

    def update(self, request, *args, **kwargs):
        try: super().update(request, *args, **kwargs)
        except Http404: super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(user = self.request.user)
        return super(MyCategoryViewSet, self).perform_create(serializer)

    def perform_update(self, serializer):
        serializer.save(user=self.request.user)
        return super(MyCategoryViewSet, self).perform_update(serializer)


class MyNewsViewSet(viewsets.ModelViewSet):
    queryset = MyNews.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = MyNewsSerializer

    def get_queryset(self):
        return MyNews.objects.filter(user = self.request.user)

    def perform_create(self, serializer):
        serializer.save(user = self.request.user)
        return super(MyNewsViewSet, self).perform_create(serializer)


class NewsView(views.APIView):

    def get(self, request, format = None):
        id = self.request.query_params.get('id', None)

        category = list(filter(None, self.request.query_params.get(
            'category', '').split(",")))

        tag = list(map(int,
            filter(None, self.request.query_params.get(
                'tag', '').split(","))))

        search = self.request.query_params.get('search', None)
        similar = self.request.query_params.get('similar', None)

        next = self.request.query_params.get('next', None)
        prev = self.request.query_params.get('prev', None)

        page = self.request.query_params.get('page', 1)

        news = News.objects.filter(visibility = True).order_by('-id')


        if search:
            news = news.annotate(
                search = SearchVector(
                    'headline', 'body', 'newsAgency', 'category__name', 'tags__name'),
            ).filter(search = search)

        if similar: news = news.get(id = similar).etags.similar_objects()

        if category:

            if "independent" in category:
                news = news.filter(independent = True)
                category.remove("independent")
            else: news = news.filter(independent = False)

            if "preference" in category:
                if request.user.is_authenticated:
                    mycategory = MyCategory.objects.filter(user = request.user)

                    if mycategory:
                        cats = MyCategorySerializer(mycategory[0]).data["categorys"]
                        news = news.filter(category__in = cats)
                    else: category.append("trending")

                else: return response.Response({"message": "User is not Authenticated"})

                category.remove("preference")

            if "trending" in category:
                time_threshold = datetime.now() - timedelta(days = 5)
                iso, hr = datetime.now(timezone.utc).isocalendar(), datetime.now().hour

                news = news.filter(created_at__gt = time_threshold).annotate(
                    popularity = (F('pos') - F('neg') + 0.01)/(
                        (iso[0] - Extract(F('created_at'), 'iso_year')) * 364 * 24 + (iso[1] - Extract(F('created_at'), 'week')) * 7 * 24 + (iso[2] - Extract(F('created_at'), 'week_day') % 7 - 1) * 24 + hr - Extract(F('created_at'), 'hour') + 1.01)
                ).order_by('-popularity')

                category.remove("trending")

            elif category: news = news.filter(category__name__in = category)
        else: news = news.filter(independent=False)

        data = {}

        news = news.distinct()

        if id:
            if next and next != "0":
                news1 = news.filter(id__gt = int(id)).order_by('id')[0:int(next)]
                serializer = NewsSerializer(news1, many = True, context = {'request': request})
                data['next'] = serializer.data

            if prev and prev != "0":
                news2 = news.filter(id__lt = int(id)).order_by('-id')[0:int(prev)]
                serializer = NewsSerializer(news2, many = True, context = {'request': request})
                data['prev'] = serializer.data
                if not next or next == "0": data['next'] = data['prev']
            else: data['prev'] = data['next']
        else:
            serializer = NewsSerializer(Paginator(news, 20).page(page), many = True, context = {'request': request})
            data['next'] =  data['prev'] = serializer.data
        return response.Response(data)


class SaveViewSet(viewsets.ModelViewSet):
    queryset = Save.objects.order_by('-created_at')
    pagination_class = StandardResultsSetPagination
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = SaveSerializer

    def get_queryset(self, *args, **kwargs):
        return Save.objects.filter(user = self.request.user).order_by('-created_at')

    def get_serializer_context(self):
        context = super(SaveViewSet, self).get_serializer_context()
        context.update({'request': self.request})
        return context

    def perform_create(self, serializer):
        serializer.save(user = self.request.user)
        return super(SaveViewSet, self).perform_create(serializer)

    def perform_update(self, serializer):
        serializer.save(user = self.request.user)
        return super(SaveViewSet, self).perform_update(serializer)


class VoteViewSet(viewsets.ModelViewSet):
    queryset = Vote.objects.order_by('-created_at')
    pagination_class = StandardResultsSetPagination
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = VoteSerializer

    def get_queryset(self, *args, **kwargs):
        return Vote.objects.filter(user = self.request.user).order_by('-created_at')

    def get_serializer_context(self):
        context = super(VoteViewSet, self).get_serializer_context()
        context.update({'request': self.request})
        return context

    def perform_create(self, serializer):
        serializer.save(user = self.request.user)
        return super(VoteViewSet, self).perform_create(serializer)

    def perform_update(self, serializer):
        serializer.save(user = self.request.user)
        return super(VoteViewSet, self).perform_update(serializer)


class OrganizationViewSet(viewsets.ModelViewSet):
    queryset = Organization.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = OrganizationSerializer
    http_method_names = ['get', 'post']


class ProfileViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ProfileSerializer
    http_method_names = ['get', 'put', 'patch', 'head']

    def get_queryset(self, *args, **kwargs):
        return User.objects.filter(id = self.request.user.id)


class ProfileInfoViewSet(viewsets.ModelViewSet):
    queryset = Profile.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ProfileInfoSerializer
    http_method_names = ['get', 'put', 'patch', 'head']

    def get_queryset(self, *args, **kwargs):
        return Profile.objects.filter(user = self.request.user)


class CompViewSet(viewsets.ViewSet):
    queryset = Comp.objects.all().order_by('-start_time')

    def list(self, request):
        queryset = Comp.objects.all().order_by('-start_time')
        return response.Response(CompSerializer(queryset, many=True).data)

    def retrieve(self, request, pk=None):
        queryset = Comp.objects.all()
        user = get_object_or_404(queryset, pk=pk)
        serializer = CompSerializer(user)
        return response.Response(serializer.data)

    @decorators.action(
        detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated]
    )
    def questions(self, request, pk=None):
        instance = Comp.objects.filter(id=pk, participants=request.user, start_time__gte=timezone.now(), end_time__lte=timezone.now())
        if instance.exists():
            ques = instance.questions.order_by('-created_at')[:40]
            return response.Response(QuestionSerializer(random.sample(ques, 15)).data)
        return response.Response([])

    @decorators.action(
        detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated]
    )
    def submission(self, request, pk=None):
        instance = Comp.objects.filter(id=pk, participants=request.user, start_time__gte=timezone.now(), end_time__lte=timezone.now())
        if instance.exists():
            ans = json.loads(request.body.decode('utf-8'))
            CompSub.objects.create(comp=pk, user=request.user, ans=ans)
            return response.Response({'success': True})
        return response.Response({'success': False})


class EventView(generics.ListAPIView):
    queryset = Event.objects.all().order_by('-start_time')
    serializer_class = EventSerializer
