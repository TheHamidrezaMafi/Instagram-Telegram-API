from django.urls import path, include
from django.contrib import admin
from app import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('webapp/', views.WebAppPageView.as_view(), name='webapp_page'),
    path('login/',views.LoginPageView.as_view(), name='login'),
    path('instagram-login/',views.instagram_login, name='instagram-login'),
    path('profile/', views.profile, name='profile'),
    path('chats/', views.chats_page, name='chats'),
    path('statistics/', views.statistics_page, name='statistics_page'),
    path('subscribe/', views.subscribe_page, name='subscribe_page'),
    path('chats/analysis/', views.chats_analysis, name='chats_analysis'),
    path('initDataUser/', views.init_data_user, name='init_data_user'),
    path('chat/<str:thread_id>/', views.direct_chat_view, name='direct_chat'),
    path('proxy-image/', views.proxy_image, name='proxy_image'),
    path('popular_products/', views.popular_products_page, name='popular_products_page'),
    path('time_analysis/', views.time_analysis_page, name='time_analysis_page'),
]