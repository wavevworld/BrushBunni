from django.urls import path
from blog import views

urlpatterns = [
    path('', views.home, name='home'),  
    path('about/', views.home, name='about'),
    path('community/', views.community, name='community'),
    path('bb-online/', views.be_online, name='be_online'),
    path('events/', views.events, name='events'),
    path('event/<slug:slug>/', views.event_detail, name='event_detail'),  
    path('shop/', views.shop, name='shop'),
    path('project-bunni/', views.project_bunni, name='project_bunni'),
    path('members/', views.members, name='members'),
    path('contact/', views.contact, name='contact'),
]
