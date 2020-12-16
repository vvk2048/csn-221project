from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.hashers import make_password
from rest_framework.utils import json
from rest_framework.views import APIView
from rest_framework.response import Response

import urllib.request, requests
from rest_framework_simplejwt.tokens import RefreshToken

from django.contrib.auth.models import User
from .models import Profile

from django.core.files import File

class Stats(APIView):
    def get(self, request, format=None):
        response = {
            "total": Profile.objects.filter(version=1).count()
        }
        return Response(response)

class GoogleLogin(APIView):
    def post(self, request):
        payload = {'access_token': request.data.get("token")}  # validate the token
        r = requests.get('https://www.googleapis.com/oauth2/v2/userinfo', params=payload)
        data = json.loads(r.text)

        if 'error' in data:
            content = {'message': 'wrong google token / this google token is already expired.'}
            return Response(content)

        new_user = False

        # create user if not exist
        try:
            user = User.objects.get(email=data.get('email'))
            if user.profile.version < request.data.get("version", 0): new_user = True

        except User.DoesNotExist:

            if data.get('verified_email') != True or 'email' not in data:
                return Response({'message': 'email is not verified'})

            user = User()
            user.username = data.get('id')
            user.first_name = data.get('given_name', '')
            user.last_name = data.get('family_name', '')
            # provider random default password
            user.password = make_password(BaseUserManager().make_random_password())
            user.email = data.get('email')
            user.save()

            new_user = True

        profile = Profile.objects.get(user = user)
        image = urllib.request.urlretrieve(data.get('picture'))
        profile.image.save(user.username+".png", File(open(image[0], 'rb')))
        profile.version = request.data.get("version", 0)
        profile.save()

        token = RefreshToken.for_user(user)  # generate token without username & password
        response = {}
        response['new_user'] = new_user
        response['username'] = user.username
        response['access_token'] = str(token.access_token)
        response['refresh_token'] = str(token)
        return Response(response)
