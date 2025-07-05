from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.shortcuts import render, redirect
from django.views.decorators.http import require_GET
from django.http import Http404
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from core.utils import instagram_api
from core.utils.mongo import users_collection , chats_collection
from core.utils.user_login_db import UserLoginDB
from core.utils.user_chat_db import UserChatDB
from django.http import HttpResponse
from urllib.parse import unquote as urlunquote
import requests
import json
import pymongo
from core.utils.tmp_logged_in_users import update_or_add_user as tmp_insta_update_or_add_user
from core.utils.tmp_logged_in_users import get_user as tmp_insta_get_user
from core.utils.tmp_logged_in_users import update_last_used as tmp_insta_update_last_used 
from core.utils.tmp_logged_in_users import delete_user as tmp_insta_delete_user

def login_check(request):
    telegram_id = request.GET.get("telegram_id")
    if not telegram_id:
        return None
    try:
        telegram_id = int(telegram_id)
        instagram_instance = tmp_insta_get_user(telegram_id)
        if instagram_instance.get_name():
            return instagram_instance
    except:
        try :
            user_db = UserLoginDB(users_collection).get_user(telegram_id)
            session_data =user_db.get("instagram_session")
            username = user_db.get("instagram_username")
            password = user_db.get("instagram_password")
            if not session_data:
                instagram_instance = instagram_api.insta_util(username=username, password=password, session=session_data)
                tmp_insta_update_or_add_user(telegram_id, instagram_instance)
                return instagram_instance
            else:
                instagram_instance = instagram_api.insta_util(username=username, password=password)
                if not instagram_instance:
                    return None
                else:
                    tmp_insta_update_or_add_user(telegram_id, instagram_instance)
                    return instagram_instance
        except :
            return None



# ✅ MAIN LOGIN VIEW (CSRF EXEMPTED)
@csrf_exempt
@api_view(['GET', 'POST'])
def instagram_login(request):
    print("request :",request)
    telegram_id = request.GET.get("telegram_id")
    print("telegram_id from instagram login:",telegram_id)
    instagram_instance = login_check(request)
    if instagram_instance:
        return redirect(request,f'/chats/?telegram_id={telegram_id}')
    try:
        if request.method == 'GET':
            telegram_id = request.GET.get("telegram_id")
            if telegram_id:
                user_data = UserLoginDB(users_collection).get_user(telegram_id)
                if not user_data or 'instagram_session' not in user_data:
                    return Response({'status': 'not_found'}, status=404)
                
                instagram_instance = instagram_api.insta_util(session=user_data['instagram_session'])
                return redirect(request, f'/chats/?telegram_id={telegram_id}')

        elif request.method == 'POST':
            
            data = request.data
            # print("Received Login Request:", data)

            username = data.get("username")
            password = data.get("password")
            code = data.get("code")  # optional 2FA code
            telegram_id = data.get("telegram_id")
            telegram_first_name = data.get("telegram_first_name")
            telegram_last_name = data.get("telegram_last_name")
            telegram_username = data.get("telegram_username")

            if code:
                user_login = instagram_api.insta_util(username=username, password=password, verification_code=code)
            else:
                user_login = instagram_api.insta_util(username=username, password=password)

            if user_login is None:
                return Response({'status': 'failed'})

            tmp_insta_update_or_add_user(int(telegram_id), user_login)
            session_data = user_login.get_session()
            UserLoginDB(users_collection).update_or_create_user(
                telegram_id=telegram_id,
                user_data={
                    'instagram_username': username,
                    'instagram_password': password,
                    'telegram_first_name': telegram_first_name,
                    'telegram_last_name': telegram_last_name,
                    'telegram_username': telegram_username,
                    'instagram_session': session_data
                }
            )

            return Response({'status': 'success', 'redirect': f'/chats/?telegram_id={telegram_id}'})

    except Exception as e:
        return Response({'status': 'error', 'message': str(e)}, status=500)

@require_GET
def profile(request):
    instagram_instance = login_check(request)
    if not instagram_instance:
        return redirect('/login/')
    try:
        return render(request, 'profile.html', {
            'user': instagram_instance.get_name(),
            'profile_pic_url': str(instagram_instance.get_profile_picture_url()),
            'subscription': 'premium',
            'time_left': '30 days',
        })
    except:
        return redirect('/login/')
    
@require_GET
def time_analysis_page(request):
    instagram_instance = login_check(request)
    if not instagram_instance:
        return redirect('/login/')
    try:
        stats_data = {
            'pie_data': {
                'labels': ['Highest (137–150)', 'Above Avg (124–137)', 'Below Avg (110–124)', 'Lowest (97–110)'],
                'values': [5, 3, 2, 2],
            },
            'line_data': {
                'labels': ['Day 1', 'Day 2', 'Day 3', 'Day 4'],
                'values': [95, 120, 130, 145],
            },
            'active_tab': 'monthly',
            'active_metric': 'new-users',
        }
        return render(request, 'time_analysis.html', {
            'user': instagram_instance.get_name(),
            'profile_pic_url': instagram_instance.get_profile_picture_url(),
            'stats': stats_data
        })
    except:
        return redirect('/login/')

@require_GET
def subscribe_page(request):
    instagram_instance = login_check(request)
    if not instagram_instance:
        return redirect('/login/')
    try:
        plans = [
            {
                "name": "Basic",
                "chat_count": "100 chats/mo",
                "most_liked": "Top 5 items",
                "emotions": "Standard Emotions",
                "time": "30 mins/day",
                "price": 5.00,
            },
            {
                "name": "Professional",
                "chat_count": "500 chats/mo",
                "most_liked": "Top 15 items",
                "emotions": "Advanced Emotions",
                "time": "2 hrs/day",
                "price": 12.99,
            },
            {
                "name": "Gold",
                "chat_count": "1000 chats/mo",
                "most_liked": "Top 30 items",
                "emotions": "Pro Emotions + Analytics",
                "time": "5 hrs/day",
                "price": 25.00,
            },
            {
                "name": "VIP",
                "chat_count": "Unlimited",
                "most_liked": "All Items",
                "emotions": "All Features Unlocked",
                "time": "Unlimited",
                "price": 49.99,
            }
        ]

        return render(request, 'subscribe.html', {
            'user': instagram_instance.get_name(),
            'profile_pic_url': instagram_instance.get_profile_picture_url(),
            'plans': plans
        })

    except:
        return redirect('/login/')
@require_GET
def chats_analysis(request):
    instagram_instance = login_check(request)
    if not instagram_instance:
        return redirect('/login/')
    try:
        emotion_data = [
            {
                "name": "Happiness",
                "slug": "happiness",
                "count": 14,
                "example": "Had such a great day today! 😊"
            },
            {
                "name": "Anger",
                "slug": "anger",
                "count": 7,
                "example": "I'm really upset about what happened. 😠"
            },
            {
                "name": "Sadness",
                "slug": "sadness",
                "count": 9,
                "example": "Feeling a bit low lately..."
            }
        ]

        category_data = [
            {
                "name": "Family",
                "slug": "family",
                "count": 10,
                "example": "Had dinner with mom and dad ❤️"
            },
            {
                "name": "Work",
                "slug": "work",
                "count": 12,
                "example": "Meeting went well, project is progressing."
            },
            {
                "name": "Friends",
                "slug": "friends",
                "count": 8,
                "example": "Had fun hanging out last night!"
            }
        ]

        return render(request, 'chats_analysis.html', {
            'user': instagram_instance.get_name(),
            'profile_pic_url': instagram_instance.get_profile_picture_url(),
            'emotions': emotion_data,
            'categories': category_data
        })
    except:
        return redirect('/login/')
    
@require_GET
def direct_chat_view(request, thread_id):
    instagram_instance = login_check(request)
    if not instagram_instance:
        return redirect('/login/')
    try:
        messages = instagram_instance.get_messages(thread_id=thread_id)
        chat = instagram_instance.get_chat_metadata(thread_id=thread_id)
        telegram_id = int(request.GET.get("telegram_id"))
        UserChatDB(chats_collection).save_or_update_chat(telegram_id, thread_id, messages)
        return render(request, 'direct_chat.html', {
            'chat': chat,
            'messages': messages,
            'user_id': str(instagram_instance.id),
            'telegram_id': telegram_id,
        })

    except Exception as e:
        raise Http404("Chat not found.")
    except:
        return redirect('/login/')

# View to render the Telegram login frontend
class WebAppPageView(APIView):
    def get(self, request):
        return render(request, 'webapp.html')


class LoginPageView(APIView):
    def get(self, request):
        instagram_instance = login_check(request)
        if not instagram_instance:
            return render(request, 'login.html')
        else:
            telegram_id = request.GET.get("telegram_id")
            return redirect(f'/chats/?telegram_id={telegram_id}')
        # return render(request, 'login.html')
# View to show chats after login
@require_GET
def chats_page(request):
    instagram_instance = login_check(request)
    if not instagram_instance:
        return redirect('/login/')
    try:
        chats = instagram_instance.get_chats()
        return render(request, 'chats.html', {'chats': chats})
    except:
        return redirect('/login/')


# For saving initial Telegram data
@csrf_exempt
@api_view(['POST'])
def init_data_user(request):
    try:
        data = request.data
        telegram_id = data.get("telegram_id")
        if not telegram_id:
            return Response({'error': 'telegram_id is required'}, status=400)

        # Save or update in MongoDB
        user_data = {
            "telegram_id": telegram_id,
            "instagram_username": data.get("username"),
            "instagram_password": data.get("password"),
            "telegram_first_name": data.get("telegram_first_name"),
            "telegram_last_name": data.get("telegram_last_name"),
            "telegram_username": data.get("telegram_username"),
            "instagram_session": data.get("session"),
        }

        created = UserLoginDB(users_collection).update_or_create_user(telegram_id, user_data)  # Implemented with upsert
        return Response({'status': 'ok', 'created': created})
    except Exception as e:
        return Response({'error': str(e)}, status=500)


@require_GET
def proxy_image(request):
    image_url = request.GET.get("url")
    if not image_url:
        return HttpResponse("Missing URL", status=400)

    try:
        decoded_url = urlunquote(image_url)
        headers = {"User-Agent": "Mozilla/5.0"}  # mimic browser
        resp = requests.get(decoded_url, headers=headers, stream=True, timeout=10)
        content_type = resp.headers.get("Content-Type", "image/jpeg")
        return HttpResponse(resp.content, content_type=content_type)
    except Exception as e:
        return HttpResponse(f"Error fetching image: {e}", status=500)
    
@require_GET
def popular_products_page(request):
    instagram_instance = login_check(request)
    if not instagram_instance:
        return redirect('/login/')
    try:
        product_data = {
            'pie_chart': {
                'labels': ['Electronics', 'Clothing', 'Books'],
                'values': [25, 40, 35],
            },
            'products': {
                'electronics': [
                    {'name': 'Smart Phone X10', 'stock': 150},
                    {'name': 'Laptop Z200', 'rating': 4.8},
                ],
                'clothing': [
                    {'name': 'Dress A20', 'stock': 75},
                    {'name': 'Jacket B12', 'rating': 4.5},
                ],
                'books': [
                    {'name': 'Book "Learn JS"', 'stock': 200},
                    {'name': 'Book "Python Basics"', 'rating': 4.7},
                ]
            }
        }

        return render(request, 'popular_products.html', {
            'user': instagram_instance.get_name(),
            'profile_pic_url': instagram_instance.get_profile_picture_url(),
            'data': product_data
        })

    except:
        return redirect('/login/')
    
@require_GET
def statistics_page(request):
    logged_in = login_check(request)
    if not logged_in:
        return redirect('/login/')
    try:
        user_count = 1500

        return render(request, 'statistics.html', {
            'user': logged_in.get_name(),
            'user_count': user_count,
        })
    except:
        return redirect('/login/')