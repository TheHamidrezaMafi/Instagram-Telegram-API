from rest_framework import serializers
from app.models import UserLogin

class UserLoginSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserLogin
        fields = '__all__'  # or list them explicitly