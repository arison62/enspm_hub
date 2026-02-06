from django.urls import include, path
from .views.feeds import HomeView, index
from .views.internships import InternshipsView
from .views.opportunites import OpportunitiesView, JobView, TrainingView
from .views.chat import ChatView
from .views.auth import LoginView
from .views.profile import ProfileView
from .views.network import NetworkView, NetworkGroupView
from .views.auth import PasswordResetView
from .views.admin import urls as admin_urls


urlpatterns = [
    path('', index),
    path('admin', include(admin_urls)),
    path('feeds', HomeView.as_view(), name='feeds'),
    
    path('network', NetworkView.as_view(), name='network'),
    path('network/groups/<slug:slug>', NetworkGroupView.as_view(), name='network_group'),
    
    path('opportunities', OpportunitiesView.as_view(), name='opportunities'),
    path('jobs/<slug:slug>', JobView.as_view(), name='job_details'),
    path('formations/<slug:slug>', TrainingView.as_view(), name='training_details'),
    
    path('chat', ChatView.as_view(), name="chat"),
    
    path('internships', InternshipsView.as_view(), name="internships"),
    path('internships/<slug:slug>', InternshipsView.as_view(), name='internship_details'),
    
    path('profile/<slug:slug>', ProfileView.as_view(), name="profile"),
    path('login', LoginView.as_view(), name='login'),
    path('password-reset', PasswordResetView.as_view(), name='password_reset'),
]
