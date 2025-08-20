from rest_framework import serializers
from ..models import Client

class ClientLoginSerializer(serializers.Serializer):
    username_or_email = serializers.CharField(max_length=100)
    password = serializers.CharField(max_length=255)

class ClientRegistrationSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=120)
    phone = serializers.CharField(max_length=30)
    username = serializers.CharField(max_length=50)
    email = serializers.EmailField(required=False, allow_blank=True)
    
    def validate_username(self, value):
        if len(value) < 3:
            raise serializers.ValidationError("Nome de usuário deve ter pelo menos 3 caracteres")
        return value
    
    def validate_phone(self, value):
        # Remove caracteres não numéricos
        phone_clean = ''.join(filter(str.isdigit, value))
        if len(phone_clean) < 10:
            raise serializers.ValidationError("Telefone deve ter pelo menos 10 dígitos")
        return value

class ClientProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = ['name', 'email']
        
    def validate_email(self, value):
        if value and Client.objects.filter(email=value).exclude(id=self.instance.id).exists():
            raise serializers.ValidationError("Este email já está sendo usado por outro cliente")
        return value