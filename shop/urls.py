from django.urls import path

from . import views

app_name = 'shop'

urlpatterns = [
    path('', views.shop_home, name='home'),
    path('product/<slug:slug>/', views.product_detail, name='product'),
    path('buy/<int:product_id>/', views.buy_product, name='buy'),
    path('inventory/', views.inventory_view, name='inventory'),
    path('equip/<int:item_id>/', views.equip_view, name='equip'),
    path('unequip/<int:item_id>/', views.unequip_view, name='unequip'),
    path('consume/<int:item_id>/', views.consume_view, name='consume'),
    path('history/', views.purchase_history_view, name='history'),
    path('wishlist/', views.wishlist_view, name='wishlist'),
    path('wishlist/toggle/<int:product_id>/', views.wishlist_toggle_view, name='wishlist_toggle'),
]
