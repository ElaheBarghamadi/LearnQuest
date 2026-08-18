from django.urls import path
from . import views

urlpatterns = [
    path('', views.math_products, name='math-products'),


    path('gcd-lcm-page/', views.gcd_lcm_view, name='gcd_lcm_form'),
    path('factorial/', views.FactorialView.as_view(), name="factorial"),

    path('pythagorean/', views.pythagorean_triangle, name="pythagorean"),
    path('calculate/', views.prime_calculator, name='calculate'),
    path('calculate-w/', views.calculate, name='calculate-w'),
    path('stats/', views.stats_view, name='stats'),
    path('discount/', views.calculate_discount, name="discount"),
    path('converter/', views.converter_view, name='converter'),
    path('linear-equation/', views.linear_equation_view, name='linear_equation'),
    path('solve_ajax/', views.solve_linear_ajax, name='solve_linear_ajax'),

]
