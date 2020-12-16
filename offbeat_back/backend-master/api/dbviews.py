import os, datetime, urllib.request, re, urllib.parse

from django.core.files import File
from rest_framework.views import APIView
from rest_framework.response import Response

os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

from api.models import *

import datetime, logging
from dateutil import parser

opener = urllib.request.build_opener()
opener.addheaders = [('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1941.0 Safari/537.36')]
urllib.request.install_opener(opener)

from PIL import Image


def add_news(headline, source, image, body, agency, tag, category, time, summary, sentiment, etags):

    if News.objects.filter(source = source): return False
    try: img = urllib.request.urlretrieve(image)
    except:
        img = list(urllib.parse.urlsplit(image))
        img[2] = urllib.parse.quote(img[2])
        img = urllib.request.urlretrieve(urllib.parse.urlunsplit(img))
    
    if type(time) == list: time = parser.parse(time[0], fuzzy = True)
    elif time: time = parser.parse(time, fuzzy = True)
    else: time = datetime.datetime.now()
    
    news = News(
        headline = headline.replace("&#8216", ""),
        time = time,
        body = summary.replace("&#8216", ""),
        newsAgency = agency,
        source = source,
        visibility = True
    )
    news.save()
    
    if tag: news.tags.add(*tag)
    if category: news.category.add(*category)
    if etags: news.etags.add(*etags)
    
    news.image.save(
        re.sub(r'[^A-Za-z0-9 ]+', '', headline).lower().replace("'", "").replace('"', '').replace(' ', '_')+".png",
        File(open(img[0], 'rb'))
    )
    
    image = Image.open(news.image.path)
    x, y = image.size
    fx, fy = 300, (y*300)//x
    
    image = image.resize((fx, fy), Image.ANTIALIAS)
    image.save(news.image.path, quality = 90, optimize=True)
    
    news.save()
    
    return True

import gspread
from oauth2client.service_account import ServiceAccountCredentials

#Authorize the API
scope = [
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/drive.file'
]

file_name = './client_key.json'

def myeval(s):
    import ast
    try: return ast.literal_eval(s)
    except: return s

class UpdateNews(APIView):
    def get(self, request, format=None):
        if request.user.is_superuser:
            category = Category.objects.all()
            tags = Tag.objects.all()

            creds = ServiceAccountCredentials.from_json_keyfile_name(file_name,scope)
            client = gspread.authorize(creds)

            sheet = client.open('news').worksheet('final')
            articles_csv = sheet.get_all_values()

            articles = []
            for k in articles_csv:
                articles.append([myeval(i) for i in k])

            all_topics = set()
            for i in articles:
                if type(i[5]) == list: all_topics.update(i[5])
                else: all_topics.add(i[5])

            for i in all_topics:
                if len(i) > 29 or Tag.objects.filter(name = i): pass
                else: Tag.objects.create(name = i)

            tags = Tag.objects.all()

            foo = {}
            for i in tags:
                foo[i.name] = i.id

            all_cat = set()
            for i in articles:
                if type(i[6]) == list: all_cat.update(i[6])
                else: all_cat.add(i[6])

            for i in all_cat:
                if len(i) > 30 or Category.objects.filter(name = i): pass
                else: Category.objects.create(name = i)

            cats = Category.objects.all()

            foo2 = {}
            for i in cats:
                foo2[i.name] = i.id

            for article in articles:
                if type(article[5]) == list: article[5] = [foo[i] for i in article[5] if i in foo]
                elif article[5] in foo: article[5] = [foo[article[5]]]
                else: article[5] = []
                
                if type(article[6]) == list: article[6] = [foo2[i] for i in article[6] if i in foo2]
                elif article[6] in foo2: article[6] = [foo2[article[6]]]
                else: article[6] = []

            response = {'invalid_news': {}, 'total_news': len(articles), 'new': 0, 'old': 0}
            for i, article in enumerate(articles):
                logger = logging.getLogger(__name__)
                try:
                    r = add_news(*article)
                    if r:
                        response['new'] += 1
                        response['last_updated_news'] = {
                            'headline': article[0],
                            'body': article[8],
                            'source': article[1],
                            'image': article[2],
                            'agency': article[4]
                        }
                    else: response['old'] += 1
                except Exception as e:
                    News.objects.filter(source=article[1]).delete()
                    logger.error(e, exc_info=True)
                    response['invalid_news'][i+1] = {"news": article[0], "error": str(e)}
                if response["new"] == int(request.query_params.get("n", 20)): break
        else: response = "FUCK OFF!!"
        return Response(response)
