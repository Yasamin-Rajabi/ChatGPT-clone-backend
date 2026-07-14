from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import (
    RegisterView, ProfileView, LinkAccountView, ListLinkedAccountsView, SwitchAccountView,
    SubscriptionStatusView, SubscriptionPlansView, PurchaseSubscriptionView,
    AIModelViewSet, AssistantViewSet, ProjectViewSet, ConversationViewSet,
    ProjectConversationsListView, MessageListCreateView, MessageAttachmentsListView
)

router = DefaultRouter()
router.register(r'models', AIModelViewSet, basename='models')
router.register(r'assistants', AssistantViewSet, basename='assistants')
router.register(r'projects', ProjectViewSet, basename='projects')
router.register(r'conversations', ConversationViewSet, basename='conversations')

urlpatterns = [
    # Auth
    path('auth/register/', RegisterView.as_view(), name='auth_register'),
    path('auth/login/', TokenObtainPairView.as_view(), name='auth_login'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/profile/', ProfileView.as_view(), name='auth_profile'),
    
    # Account Linking / Switching
    path('auth/link-account/', LinkAccountView.as_view(), name='link_account'),
    path('auth/linked-accounts/', ListLinkedAccountsView.as_view(), name='linked_accounts'),
    path('auth/switch/', SwitchAccountView.as_view(), name='switch_account'),
    
    # Subscriptions
    path('subscription/status/', SubscriptionStatusView.as_view(), name='sub_status'),
    path('subscription/plans/', SubscriptionPlansView.as_view(), name='sub_plans'),
    path('subscription/purchase/', PurchaseSubscriptionView.as_view(), name='sub_purchase'),
    
    # Projects nested conversations
    path('projects/<int:project_id>/conversations/', ProjectConversationsListView.as_view(), name='project_conversations'),
    
    # Messages in Chatbot
    path('conversations/<int:conversation_id>/messages/', MessageListCreateView.as_view(), name='conversation_messages'),
    path('messages/<int:message_id>/attachments/', MessageAttachmentsListView.as_view(), name='message_attachments'),

    # Router URLs
    path('', include(router.urls)),
]