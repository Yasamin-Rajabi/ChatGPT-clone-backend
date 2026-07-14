from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    class SubscriptionType(models.TextChoices):
        FREE = 'FREE', 'Free'
        PREMIUM = 'PREMIUM', 'Premium'
        
    email = models.EmailField(unique=True)
    subscription_type = models.CharField(
        max_length=10, 
        choices=SubscriptionType.choices, 
        default=SubscriptionType.FREE
    )
    linked_accounts = models.ManyToManyField('self', blank=True, symmetrical=True)

    def __str__(self):
        return self.username

class Project(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='projects')

    def __str__(self):
        return self.title

class AIModel(models.Model):
    name = models.CharField(max_length=100, unique=True)
    provider = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class Assistant(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    system_prompt = models.TextField()
    is_public = models.BooleanField(default=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assistants', blank=True, null=True)

    def __str__(self):
        return self.title

class ConversationManager(models.Manager):
    def get_queryset(self):
        # به طور پیش‌فرض چت‌های حذف شده فیزیکی نمایش داده نمی‌شوند (Soft Delete)
        return super().get_queryset().exclude(status='DELETED')

class Conversation(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Active'
        ARCHIVED = 'ARCHIVED', 'Archived'
        DELETED = 'DELETED', 'Deleted'

    title = models.CharField(max_length=255, blank=True, default="New Conversation")
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE)
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='conversations')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='conversations', blank=True, null=True)
    ai_model = models.ForeignKey(AIModel, on_delete=models.PROTECT, related_name='conversations')
    assistant = models.ForeignKey(Assistant, on_delete=models.SET_NULL, related_name='conversations', blank=True, null=True)

    objects = ConversationManager()
    all_objects = models.Manager() # برای دسترسی احتمالی بک‌سورس به موارد حذف شده

    def __str__(self):
        return self.title

class Message(models.Model):
    class Role(models.TextChoices):
        USER = 'USER', 'User'
        SYSTEM = 'SYSTEM', 'System'
        ASSISTANT = 'ASSISTANT', 'Assistant'

    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    text = models.TextField()
    sender_role = models.CharField(max_length=10, choices=Role.choices)
    sent_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender_role}: {self.text[:20]}"

class Attachment(models.Model):
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='attachments')
    # کلمه upload_with به upload_to تغییر یافت:
    file = models.FileField(upload_to='attachments/') 
    file_format = models.CharField(max_length=50)
    file_size = models.IntegerField() # بر حسب بایت

    def __str__(self):
        return f"Attachment for Message {self.message.id}"