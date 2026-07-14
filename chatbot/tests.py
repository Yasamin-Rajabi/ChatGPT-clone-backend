from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from .models import AIModel, Project, Conversation, Assistant

User = get_user_model()

class ChatbotSystemTests(APITestCase):

    def setUp(self):
        # کاربر نمونه اول
        self.user1 = User.objects.create_user(username="yasamin", email="yasamin@example.com", password="password123")
        # کاربر نمونه دوم برای تست ایزوله‌سازی داده‌ها
        self.user2 = User.objects.create_user(username="bob", email="bob@example.com", password="password123")
        
        # ایجاد مدل هوش مصنوعی پایه
        self.base_model = AIModel.objects.create(name="GPT-3.5", provider="OpenAI", is_active=True)
        self.advanced_model = AIModel.objects.create(name="GPT-4", provider="OpenAI", is_active=True)
        
        # دریافت توکن برای کاربر اول
        login_url = reverse('auth_login')
        response = self.client.post(login_url, {'username': 'yasamin', 'password': 'password123'})
        self.token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token)

    # تست ۱: ثبت نام کاربر جدید
    def test_user_registration(self):
        url = reverse('auth_register')
        data = {'username': 'newuser', 'email': 'newuser@example.com', 'password': 'securepassword'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    # test ۲: ورود و دریافت توکن JWT
    def test_user_login(self):
        url = reverse('auth_login')
        data = {'username': 'yasamin', 'password': 'password123'}
        response = self.client.post(url, data)
        self.assertIn('access', response.data)

    # تست ۳: ایجاد یک پروژه جدید
    def test_create_project(self):
        url = reverse('projects-list')
        data = {'title': 'University Project', 'description': 'HW3 Workspace'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Project.objects.filter(user=self.user1).count(), 1)

    # تست ۴: ایزوله بودن اطلاعات پروژه‌های کاربران از یکدیگر (حفاظت دسترسی)
    def test_project_isolation(self):
        project_bob = Project.objects.create(title="Bob Secret Project", user=self.user2)
        url = reverse('projects-detail', args=[project_bob.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # تست ۵: ایجاد مکالمه جدید توسط کاربر رایگان با مدل پایه
    def test_create_conversation_free_tier(self):
        url = reverse('conversations-list')
        data = {'title': 'Study Chat', 'ai_model': self.base_model.id}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    # تست ۶: عدم دسترسی کاربر رایگان به مدل‌های پیشرفته (مانند GPT-4)
    def test_restrict_advanced_model_for_free_user(self):
        url = reverse('conversations-list')
        data = {'title': 'Advanced Chat', 'ai_model': self.advanced_model.id}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # تست ۷: خرید موفقیت‌آمیز اشتراک ویژه و ارتقا اکانت
    def test_purchase_subscription(self):
        url = reverse('sub_purchase')
        response = self.client.post(url)
        self.user1.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.user1.subscription_type, 'PREMIUM')

    # تست ۸: ارسال پیام جدید و دریافت پاسخ شبیه‌سازی شده (Mock) از مدل
    def test_send_message_and_get_mock_response(self):
        conv = Conversation.objects.create(title="Test Chat", user=self.user1, ai_model=self.base_model)
        url = reverse('conversation_messages', args=[conv.id])
        data = {'text': 'Hello, chatbot!'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # باید دو پیام وجود داشته باشد: یکی کاربر و یکی پاسخ بات
        self.assertEqual(conv.messages.count(), 2)

    # تست ۹: حذف منطقی چت (Soft Delete) به جای حذف فیزیکی
    def test_conversation_soft_delete(self):
        conv = Conversation.objects.create(title="To Be Deleted", user=self.user1, ai_model=self.base_model)
        url = reverse('conversations-detail', args=[conv.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        # بررسی اینکه در کوئری‌های عادی فیلتر شده اما فیزیکی حذف نشده است
        self.assertEqual(Conversation.objects.filter(id=conv.id).count(), 0)
        self.assertEqual(Conversation.all_objects.filter(id=conv.id).count(), 1)

    # تست ۱۰: امکان متصل کردن دو اکانت کاربری به یکدیگر (Link Account)
    def test_link_accounts(self):
        url = reverse('link_account')
        data = {'username': 'bob', 'password': 'password123'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(self.user2, self.user1.linked_accounts.all())