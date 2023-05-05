from django.urls import path
from .views import (
    LoginView,
    VendorRegisterView,
    CustomerRegisterView,
    VendorList,
    VendorProfileAPIView,
    VendorDetailAPIView,
    CustomerList,
    DashboardUser,
    ReferralDetailAPIView,
    AddToReferralAPIView,
    AddReferralCodeOtherAPIView,
    ShowCustomerReferralAPIView,
)

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('vendor/register/', VendorRegisterView.as_view(), name='vendor-register'),
    path('customer/register/', CustomerRegisterView.as_view(), name='customer-register'),

    path('vendor/list/', VendorList.as_view(), name='vendor-list'),
    path('customer/list/', CustomerList.as_view(), name='customer-list'),

    path('vendor/profile/<str:token>/', VendorProfileAPIView.as_view(), name='vendor-profile'),

    path('vendor/detail/<int:id>/', VendorDetailAPIView.as_view(), name='vendor-detail'),

    path('dashboard/', DashboardUser.as_view(), name='user-dashboard'),

    path('referral-info/<int:id>/', ReferralDetailAPIView.as_view(), name='referral-info'),
    path('referral-add/<int:user_id>/', AddToReferralAPIView.as_view(), name='referral-add'),
    path('referral-add-boom/<int:id>/', AddReferralCodeOtherAPIView.as_view(), name='referral-add-boom'),
    path('refer/<int:id>/', ShowCustomerReferralAPIView.as_view(), name='referral-add-boom')
]
