# web/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # Home & Dashboard
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('ai-suggestions/', views.ai_suggestions, name='ai_suggestions'),

    # Stock Search & Detail
    path('search/', views.stock_search, name='stock_search'),
    path('stock/<str:symbol>/', views.stock_detail, name='stock_detail'),
    path('stock/<str:symbol>/risk/', views.risk_analysis, name='risk_analysis'),

    # Portfolio Management
    path('portfolios/', views.portfolio_list, name='portfolio_list'),
    path('portfolios/create/', views.portfolio_create, name='portfolio_create'),
    path('portfolios/<int:portfolio_id>/', views.portfolio_detail, name='portfolio_detail'),
    path('portfolios/<int:portfolio_id>/add-holding/', views.portfolio_add_holding, name='portfolio_add_holding'),
    path('portfolios/holding/<int:holding_id>/remove/', views.portfolio_remove_holding, name='portfolio_remove_holding'),

    # Watchlist
    path('watchlist/', views.watchlist_view, name='watchlist'),
    path('watchlist/add/', views.watchlist_add, name='watchlist_add'),
    path('watchlist/<int:watchlist_id>/remove/', views.watchlist_remove, name='watchlist_remove'),

    # SIP Calculator
    path('sip/', views.sip_calculator_view, name='sip_calculator'),
    path('sip/plans/<int:plan_id>/', views.sip_plan_detail, name='sip_plan_detail'),
    path('sip/plans/<int:plan_id>/delete/', views.sip_plan_delete, name='sip_plan_delete'),

    # API Endpoints
    path('api/stock/<str:symbol>/price/', views.api_stock_price, name='api_stock_price'),
    path('api/search/', views.api_search_symbols, name='api_search_symbols'),
    path('api/portfolio/<int:portfolio_id>/refresh/', views.api_portfolio_refresh, name='api_portfolio_refresh'),
]
