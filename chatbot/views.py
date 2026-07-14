from rest_framework import viewsets, generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.shortcuts import get_object_or_404
from django.db import transaction
from .models import User, Project, AIModel, Assistant, Conversation, Message, Attachment
from .serializers import (
    UserRegisterSerializer, UserProfileSerializer, ProjectSerializer,
    AIModelSerializer, AssistantSerializer, ConversationSerializer, MessageSerializer
)
from .permissions import IsOwnerOnly, IsAssistantOwnerOrPublic, IsSuperuserOrReadOnly
from .throttles import SubscriptionRateThrottle

from drf_spectacular.utils import extend_schema_view, extend_schema, inline_serializer
from rest_framework import serializers
# --- بخش احراز هویت و مدیریت اکانت ---

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = [permissions.AllowAny]
    serializer_class = UserRegisterSerializer

class ProfileView(generics.RetrieveUpdateAPIView):
    queryset = User.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserProfileSerializer

    def get_object(self):
        return self.request.user

class LinkAccountView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        request=inline_serializer(
            name='LinkAccountRequest',
            fields={
                'username': serializers.CharField(),
                'password': serializers.CharField()
            }
        ),
        responses={200: inline_serializer(
            name='LinkAccountResponse',
            fields={'detail': serializers.CharField()}
        )}
    )

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        
        if not username or not password:
            return Response({"error": "Username and password are required."}, status=status.HTTP_400_BAD_REQUEST)
            
        target_user = get_object_or_404(User, username=username)
        
        # جلوگیری از لینک کردن اکانت خود به خود!
        if target_user == request.user:
            return Response({"error": "You cannot link your account to itself."}, status=status.HTTP_400_BAD_REQUEST)
        
        if target_user.check_password(password):
            request.user.linked_accounts.add(target_user)
            return Response({"detail": "Accounts linked successfully."}, status=status.HTTP_200_OK)
        return Response({"error": "Invalid credentials for target account."}, status=status.HTTP_400_BAD_REQUEST)

class ListLinkedAccountsView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserProfileSerializer

    def get_queryset(self):
        return self.request.user.linked_accounts.all()

class SwitchAccountView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        request=inline_serializer(
            name='SwitchAccountRequest',
            fields={'user_id': serializers.IntegerField()}
        ),
        responses={200: inline_serializer(
            name='SwitchAccountResponse',
            fields={
                'refresh': serializers.CharField(),
                'access': serializers.CharField(),
                'user': serializers.CharField()
            }
        )}
    )

    def post(self, request):
        target_user_id = request.data.get('user_id')
        target_user = get_object_or_404(User, id=target_user_id)

        if target_user in request.user.linked_accounts.all() or target_user == request.user:
            refresh = RefreshToken.for_user(target_user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': target_user.username
            })
        return Response({"error": "Account not linked."}, status=status.HTTP_403_FORBIDDEN)


# --- بخش اشتراک ---

class SubscriptionStatusView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        responses={200: inline_serializer(
            name='SubscriptionStatusResponse',
            fields={
                'subscription_type': serializers.CharField(),
                'daily_quota_remaining': serializers.CharField()
            }
        )}
    )

    def get(self, request):
        # شبیه‌سازی اطلاعات سهمیه
        tier = request.user.subscription_type
        remaining = "Unlimited" if tier == "PREMIUM" else "Dynamic (Max 50/day)"
        return Response({
            "subscription_type": tier,
            "daily_quota_remaining": remaining
        })

class SubscriptionPlansView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        responses={200: inline_serializer(
            name='SubscriptionPlansResponse',
            many=True,
            fields={
                'plan_name': serializers.CharField(),
                'price': serializers.CharField(),
                'features': serializers.CharField()
            }
        )}
    )

    def get(self, request):
        return Response([
            {"plan_name": "Free Tier", "price": "0$ / month", "features": "Access to GPT-3.5, 50 messages/day"},
            {"plan_name": "Premium Tier", "price": "20$ / month", "features": "Access to all models, Unlimited usage, File attachments"}
        ])

class PurchaseSubscriptionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        request=None, 
        responses={200: inline_serializer(
            name='PurchaseSubscriptionResponse',
            fields={'detail': serializers.CharField()}
        )}
    )

    def post(self, request):
        user = request.user
        user.subscription_type = User.SubscriptionType.PREMIUM
        user.save()
        return Response({"detail": "Upgraded to Premium successfully."}, status=status.HTTP_200_OK)


# --- بخش مدل‌های هوش مصنوعی و دستیارها ---

class AIModelViewSet(viewsets.ModelViewSet):
    queryset = AIModel.objects.filter(is_active=True)
    serializer_class = AIModelSerializer
    permission_classes = [permissions.IsAuthenticated, IsSuperuserOrReadOnly]


class AssistantViewSet(viewsets.ModelViewSet):
    serializer_class = AssistantSerializer
    permission_classes = [permissions.IsAuthenticated, IsAssistantOwnerOrPublic]
    lookup_value_regex = r'[0-9]+'
    
    def get_queryset(self):
        # نمایش دستیارهای عمومی + دستیارهای اختصاصی خود کاربر
        return Assistant.objects.filter(is_public=True) | Assistant.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


# --- بخش پروژه‌ها ---

class ProjectViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOnly]
    lookup_value_regex = r'[0-9]+'

    def get_queryset(self):
        return Project.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def destroy(self, request, *args, **kwargs):
        # با حذف پروژه تمام مکالمات آن هم حذف می‌شوند (مدیریت شده در مدل‌ها با Cascade)
        return super().destroy(request, *args, **kwargs)


# --- بخش مکالمات و پیام‌ها ---

class ConversationViewSet(viewsets.ModelViewSet):
    serializer_class = ConversationSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOnly]
    lookup_value_regex = r'[0-9]+'

    def get_queryset(self):
        return Conversation.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        # بررسی دسترسی به مدل بر اساس نوع اشتراک
        ai_model = serializer.validated_data.get('ai_model')
        if "4" in ai_model.name or "Claude" in ai_model.name:
            if self.request.user.subscription_type != User.SubscriptionType.PREMIUM:
                from rest_framework.exceptions import ValidationError
                raise ValidationError("Advanced models are only available for Premium subscribers.")
        serializer.save(user=self.request.user)

    def destroy(self, request, *args, **kwargs):
        # پیاده‌سازی فرآیند حذف منطقی (Soft Delete) بر اساس نیازمندی صورت‌مسئله
        conversation = self.get_object()
        conversation.status = Conversation.Status.DELETED
        conversation.save()
        return Response({"detail": "Conversation soft deleted successfully."}, status=status.HTTP_204_NO_CONTENT)


class ProjectConversationsListView(generics.ListAPIView):
    serializer_class = ConversationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        project_id = self.kwargs['project_id']
        project = get_object_or_404(Project, id=project_id, user=self.request.user)
        return Conversation.objects.filter(project=project)


@extend_schema_view(
    post=extend_schema(
        request={
            'application/json': inline_serializer(
                name='MessageJsonRequest',
                fields={
                    'text': serializers.CharField()
                }
            ),
            'multipart/form-data': {
                'type': 'object',
                'properties': {
                    'text': {'type': 'string'},
                    'file': {
                        'type': 'string',
                        'format': 'binary',
                    },
                },
                'required': ['text'],
            }
        }
    )
)

class MessageListCreateView(generics.ListCreateAPIView):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [SubscriptionRateThrottle]
    throttle_scope = 'free_user_tier'

    def get_queryset(self):
        conversation_id = self.kwargs['conversation_id']
        conversation = get_object_or_404(Conversation, id=conversation_id, user=self.request.user)
        return Message.objects.filter(conversation=conversation).order_by('sent_at')

    def perform_create(self, serializer):
        conversation_id = self.kwargs['conversation_id']
        conversation = get_object_or_404(Conversation, id=conversation_id, user=self.request.user)

        uploaded_file = self.request.FILES.get('file')
        if uploaded_file and self.request.user.subscription_type != User.SubscriptionType.PREMIUM:
            from rest_framework.exceptions import ValidationError
            raise ValidationError("File attachment upload is restricted to Premium users.")

        with transaction.atomic():
            user_message = serializer.save(sender_role=Message.Role.USER, conversation=conversation)

            if uploaded_file:
                Attachment.objects.create(
                    message=user_message,
                    file=uploaded_file,
                    file_format=uploaded_file.name.split('.')[-1] if '.' in uploaded_file.name else 'unknown',
                    file_size=uploaded_file.size
                )

            mock_text = f"This is a mocked response from model '{conversation.ai_model.name}'"
            if conversation.assistant:
                mock_text += f" acting as assistant: '{conversation.assistant.title}'."

            Message.objects.create(
                conversation=conversation,
                text=mock_text,
                sender_role=Message.Role.ASSISTANT
            )


class MessageAttachmentsListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        responses={200: inline_serializer(
            name='MessageAttachmentsResponse',
            many=True,
            fields={
                'id': serializers.IntegerField(),
                'file_url': serializers.CharField(),
                'format': serializers.CharField(),
                'size': serializers.IntegerField()
            }
        )}
    )

    def get(self, request, message_id):
        message = get_object_or_404(Message, id=message_id, conversation__user=request.user)
        attachments = message.attachments.all()
        data = [{"id": att.id, "file_url": att.file.url, "format": att.file_format, "size": att.file_size} for att in attachments]
        return Response(data)