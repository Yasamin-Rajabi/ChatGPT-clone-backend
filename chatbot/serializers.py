from rest_framework import serializers
from .models import User, Project, AIModel, Assistant, Conversation, Message, Attachment

class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'subscription_type']
        read_only_fields = ['username', 'email', 'subscription_type']

class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = '__all__'
        read_only_fields = ['user']

class AIModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIModel
        fields = '__all__'

class AssistantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assistant
        fields = '__all__'
        read_only_fields = ['user']

class ConversationSerializer(serializers.ModelSerializer):
    title = serializers.CharField(default="Debug Python Codes", required=False)
    ai_model = serializers.IntegerField(default=1, help_text="ID of the AI Model")
    project = serializers.IntegerField(default=1, required=False, help_text="ID of the Project")

    class Meta:
        model = Conversation
        fields = '__all__'
        read_only_fields = ['user']

    def validate_project(self, value):
        if value and value.user != self.context['request'].user:
            raise serializers.ValidationError("This project does not belong to you.")
        return value

class AttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attachment
        fields = '__all__'

class MessageSerializer(serializers.ModelSerializer):
    attachments = AttachmentSerializer(many=True, read_only=True)
    sender_role = serializers.CharField(read_only=True)
    sent_at = serializers.DateTimeField(read_only=True)
    
    # تعریف صریح فیلد به عنوان فایل آپلود شونده
    text = serializers.CharField(default="Explain the DFS algorithm in simple terms.")
    file = serializers.FileField(required=False, write_only=True, allow_empty_file=False)

    class Meta:
        model = Message
        fields = ['id', 'sender_role', 'text', 'sent_at', 'attachments', 'file']
        read_only_fields = ['id', 'sender_role', 'sent_at', 'attachments']

    def validate_conversation(self, value):
        # بررسی دسترسی کاربر به مکالمه
        if value.user != self.context['request'].user:
            raise serializers.ValidationError("You do not have access to this conversation.")
        return value
    
    def create(self, validated_data):
        # فیلد file فقط جهت دریافت ورودی از کلاینت است؛
        # ذخیره واقعی Attachment در MessageListCreateView.perform_create انجام می‌شود
        validated_data.pop('file', None)
        return super().create(validated_data)
    

    # def create(self, validated_data):
    #     file = validated_data.pop('file', None)
    #     message = super().create(validated_data)
        
    #     if file and self.context['request'].user.subscription_type == 'PREMIUM':
    #         from chatbot.models import MessageAttachment
    #         MessageAttachment.objects.create(
    #             message=message,
    #             file=file,
    #             file_format=file.name.split('.')[-1] if '.' in file.name else 'unknown',
    #             file_size=file.size
    #         )
    #     return message