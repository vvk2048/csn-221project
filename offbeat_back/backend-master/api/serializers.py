from django.contrib.auth.models import User
from rest_framework import serializers

from .models import *

class SubscriptionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        fields = '__all__'


class DiscountCouponSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiscountCoupon
        fields = '__all__'


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = '__all__'


class ProfileInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = '__all__'
        read_only_fields = ['plan_type', 'expiry_date', 'version']

    def to_representation(self, instance):
        response = super().to_representation(instance)
        response["org"] = OrganizationSerializer(instance.org).data
        response["plan_type"] = OrganizationSerializer(instance.plan_type).data
        return response


class ProfileSerializer(serializers.ModelSerializer):
    profile = ProfileInfoSerializer()

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'profile']
        read_only_fields = ['username', 'email', 'profile']


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'


class TopicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Topic
        fields = '__all__'


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'


class QuoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Quote
        fields = '__all__'


class MyTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = MyTag
        fields = '__all__'
        read_only_fields = ['user']

    def to_representation(self, instance):
        response = super().to_representation(instance)
        response["tags"] = TagSerializer(instance.tags, many=True).data
        return response


class MyCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = MyCategory
        fields = '__all__'
        read_only_fields = ['user']

    def to_representation(self, instance):
        response = super().to_representation(instance)
        response["categorys"] = CategorySerializer(instance.categorys, many=True).data
        return response

class SSerializer(serializers.ModelSerializer):
    class Meta:
        model = Save
        fields = '__all__'
        read_only_fields = ['user']

class VSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vote
        fields = '__all__'
        read_only_fields = ['user']

class NewsSerializer(serializers.ModelSerializer):
    class Meta:
        model = News
        exclude = ['tags']

    def to_representation(self, instance):
        request = self.context.get("request")
        response = super().to_representation(instance)
        response["category"] = CategorySerializer(instance.category, many=True).data
        response["username"] = instance.user.get_full_name() if instance.user else None
        response["image"] = request.build_absolute_uri(instance.image.url) if instance.image else None
        if request.user.is_authenticated:
            i = instance.bookmark.filter(user=request.user)
            response["save"] = SSerializer(i[0]).data if i else None
            i = instance.vote.filter(user=request.user)
            response["vote"] = VSerializer(i[0]).data if i else None
        else:
            response["save"] = None
            response["vote"] = None
        return response


class SaveSerializer(serializers.ModelSerializer):
    class Meta:
        model = Save
        fields = '__all__'
        read_only_fields = ['user']

    def to_representation(self, instance):
        response = super().to_representation(instance)
        response["news"] = NewsSerializer(instance.news, context=self.context).data
        return response


class VoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vote
        fields = '__all__'
        read_only_fields = ['user']

    def to_representation(self, instance):
        response = super().to_representation(instance)
        response["news"] = NewsSerializer(instance.new, context=self.context).data
        return response


class MyNewsSerializer(serializers.ModelSerializer):
    class Meta:
        model = MyNews
        fields = '__all__'
        read_only_fields = ['user', 'created_at', 'news']


class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ['question']


class CompSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comp
        fields = ['name', 'org', 'type', 'about', 'fee', 'start_time', 'end_time']

    def to_representation(self, instance):
        response = super().to_representation(instance)
        response["org"] = OrganizationSerializer(instance.org).data
        return response


class CompSubSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompSub
        fields = '__all__'
        read_only_fields = ['time']


class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = '__all__'
        read_only_fields = ['user']

    def to_representation(self, instance):
        response = super().to_representation(instance)
        response["org"] = OrganizationSerializer(instance.org).data
        response["comp"] = OrganizationSerializer(instance.comp, many=True).data
        return response
