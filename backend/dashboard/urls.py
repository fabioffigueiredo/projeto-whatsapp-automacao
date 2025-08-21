from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    # Dashboard principal
    path('', views.DashboardView.as_view(), name='index'),
    
    # APIs do dashboard
    path('api/stats/', views.DashboardStatsView.as_view(), name='stats'),
    path('api/messages-chart/', views.MessageChartView.as_view(), name='messages_chart'),
    path('api/recent-messages/', views.RecentMessagesView.as_view(), name='recent_messages'),
    path('api/health/', views.SystemHealthView.as_view(), name='health'),
    path('api/campaigns/', views.CampaignStatsView.as_view(), name='campaigns'),
]