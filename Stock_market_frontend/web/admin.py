# web/admin.py

from django.contrib import admin
from .models import Portfolio, PortfolioHolding, Watchlist, SIPPlan, StockAlert

@admin.register(Portfolio)
class PortfolioAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at', 'updated_at']
    search_fields = ['name', 'description']
    date_hierarchy = 'created_at'

@admin.register(PortfolioHolding)
class PortfolioHoldingAdmin(admin.ModelAdmin):
    list_display = ['symbol', 'portfolio', 'quantity', 'avg_price', 'current_price']
    list_filter = ['portfolio']
    search_fields = ['symbol', 'company_name']

@admin.register(Watchlist)
class WatchlistAdmin(admin.ModelAdmin):
    list_display = ['symbol', 'company_name', 'target_price', 'added_at']
    search_fields = ['symbol', 'company_name']
    date_hierarchy = 'added_at'

@admin.register(SIPPlan)
class SIPPlanAdmin(admin.ModelAdmin):
    list_display = ['name', 'monthly_investment', 'years', 'annual_return', 'created_at']
    search_fields = ['name']
    date_hierarchy = 'created_at'

@admin.register(StockAlert)
class StockAlertAdmin(admin.ModelAdmin):
    list_display = ['symbol', 'alert_type', 'threshold', 'is_active', 'triggered', 'created_at']
    list_filter = ['alert_type', 'is_active', 'triggered']
    search_fields = ['symbol']
