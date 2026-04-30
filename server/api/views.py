import joblib
import numpy as np
import os
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.authtoken.models import Token
from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth import login
from .models import ThreatLog

# 🔹 Load Model & Scaler
MODEL_PATH = os.path.join(settings.BASE_DIR, 'api/ai_module/cyber_model.pkl')
SCALER_PATH = os.path.join(settings.BASE_DIR, 'api/ai_module/scaler.pkl')

try:
    model = joblib.load(MODEL_PATH)
    scaler = joblib.load(SCALER_PATH)
except Exception as e:
    print(f"Error loading AI assets: {e}")


# 🔹 AI Detection
@api_view(['POST'])
def detect_threat(request):
    try:
        features = request.data.get('features')

        if not isinstance(features, list) or len(features) != 41:
            return Response({"error": "Invalid features. Need 41 values."}, status=400)

        input_data = np.array(features).reshape(1, -1)
        input_scaled = scaler.transform(input_data)

        prediction = model.predict(input_scaled)
        probability = model.predict_proba(input_scaled)

        is_attack = bool(prediction[0])
        confidence = float(np.max(probability))

        status = "ATTACK" if is_attack else "NORMAL"
        action = "Blocked" if is_attack else "Logged"

        severity = "Low"
        if is_attack:
            severity = "Critical" if confidence > 0.9 else "High"

        ThreatLog.objects.create(
            event_type="Intrusion Attempt" if is_attack else "Standard Traffic",
            severity=severity,
            confidence=confidence,
            action_taken=action,
            src_ip=request.META.get('REMOTE_ADDR', '127.0.0.1')
        )

        return Response({
            "status": status,
            "confidence": round(confidence, 4),
            "action": "BLOCK_IP" if is_attack else "NONE",
            "message": "AI Analysis Complete & Logged"
        })

    except Exception as e:
        return Response({"error": str(e)}, status=500)


# 🔹 Get Logs
@api_view(['GET'])
def get_logs(request):
    try:
        logs = ThreatLog.objects.all().order_by('-timestamp')[:15]

        formatted_logs = [
            {
                "id": log.id,
                "time": log.timestamp.strftime("%H:%M:%S"),
                "ip": log.src_ip,
                "event": log.event_type,
                "severity": log.severity,
                "status": log.action_taken,
                "confidence": log.confidence
            } for log in logs
        ]

        return Response(formatted_logs)

    except Exception as e:
        return Response({"error": str(e)}, status=500)
# 🔐 Login API (Token based)
@api_view(['POST'])
def login_view(request):
    try:
        username = request.data.get('username')
        password = request.data.get('password')

        user = authenticate(username=username, password=password)

        if user is not None:
            token, created = Token.objects.get_or_create(user=user)

            return Response({
                "message": "Login successful",
                "token": token.key,
                "username": user.username
            })
        else:
            return Response({"error": "Invalid credentials"}, status=400)

    except Exception as e:
        print("LOGIN ERROR:", e)
        return Response({"error": str(e)}, status=500)


# 🚪 Logout API
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    request.user.auth_token.delete()
    return Response({"message": "Logged out"})


# 🔐 Check Auth
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_auth(request):
    return Response({"authenticated": True})    

from django.contrib.auth.models import User

# 📝 Register API
@api_view(['POST'])
def register_view(request):
    try:
        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            return Response({"error": "Username and password required"}, status=400)

        if User.objects.filter(username=username).exists():
            return Response({"error": "Username already exists"}, status=400)

        user = User.objects.create_user(username=username, password=password)
        return Response({"message": "User created successfully"})
    except Exception as e:
        return Response({"error": str(e)}, status=500)

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import base64
from django.utils import timezone
from datetime import timedelta

@api_view(['GET'])
def get_stats(request):
    try:
        now = timezone.now()
        start = now - timedelta(hours=24)
        logs = ThreatLog.objects.filter(timestamp__gte=start)
        
        active_threats = logs.filter(action_taken="Blocked").count()
        packets_scanned = logs.count() + 15000 
        last_attack = logs.filter(action_taken="Blocked").first()
        
        return Response({
            "active_threats": active_threats,
            "packets_scanned": f"{packets_scanned:,}",
            "last_attack": last_attack.timestamp.strftime("%H:%M:%S") if last_attack else "None"
        })
    except Exception as e:
        return Response({"error": str(e)}, status=500)

@api_view(['GET'])
def get_attack_graph(request):
    try:
        now = timezone.now()
        start = now - timedelta(hours=12)
        logs = ThreatLog.objects.filter(timestamp__gte=start)
        
        hours = []
        counts = []
        
        for i in range(12):
            hour_start = start + timedelta(hours=i)
            hour_end = start + timedelta(hours=i+1)
            c = logs.filter(timestamp__gte=hour_start, timestamp__lt=hour_end, action_taken="Blocked").count()
            hours.append(hour_start.strftime("%H:00"))
            counts.append(c)
            
        plt.figure(figsize=(8, 4), facecolor='#0f172a') 
        ax = plt.gca()
        ax.set_facecolor('#0f172a')
        
        plt.bar(hours, counts, color='#10b981')
        plt.title('Blocked Attacks (12h)', color='white')
        plt.xlabel('Time', color='white')
        plt.ylabel('Attacks Blocked', color='white')
        plt.xticks(rotation=45, color='gray')
        plt.yticks(color='gray')
        
        ax.spines['bottom'].set_color('#1e293b')
        ax.spines['top'].set_color('#1e293b') 
        ax.spines['right'].set_color('#1e293b')
        ax.spines['left'].set_color('#1e293b')

        plt.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        plt.close()
        buf.seek(0)
        
        image_base64 = base64.b64encode(buf.read()).decode('utf-8')
        
        return Response({"image": "data:image/png;base64," + image_base64})
    except Exception as e:
        return Response({"error": str(e)}, status=500)
