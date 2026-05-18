from django.urls import path
from . import views

app_name = 'lab'

urlpatterns = [
    path('dashboard/', views.LabDashboardView.as_view(), name='dashboard'),
    path('orders/', views.LabOrderListView.as_view(), name='order_list'),
    path('orders/<int:order_id>/', views.LabOrderDetailView.as_view(), name='order_detail'),
]
