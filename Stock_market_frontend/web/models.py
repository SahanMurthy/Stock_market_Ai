# web/models.py

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone

class Portfolio(models.Model):
    """User portfolio/watchlist"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    @property
    def total_value(self):
        return sum(holding.current_value for holding in self.holdings.all())

    @property
    def total_invested(self):
        return sum(holding.invested_value for holding in self.holdings.all())

    @property
    def total_pnl(self):
        return self.total_value - self.total_invested


class PortfolioHolding(models.Model):
    """Individual stock holdings in a portfolio"""
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name='holdings')
    symbol = models.CharField(max_length=20)
    company_name = models.CharField(max_length=200, blank=True)
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    avg_price = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    current_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    invested_value = models.DecimalField(max_digits=15, decimal_places=2)
    current_value = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    purchase_date = models.DateField(default=timezone.now)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['symbol']
        unique_together = ['portfolio', 'symbol']

    def __str__(self):
        return f"{self.symbol} ({self.quantity} shares)"

    @property
    def pnl(self):
        return self.current_value - self.invested_value

    @property
    def pnl_percent(self):
        if self.invested_value > 0:
            return ((self.current_value - self.invested_value) / self.invested_value) * 100
        return 0

    def save(self, *args, **kwargs):
        # Auto-calculate invested value
        self.invested_value = float(self.avg_price) * self.quantity
        # Calculate current value if current_price is set
        if self.current_price > 0:
            self.current_value = float(self.current_price) * self.quantity
        super().save(*args, **kwargs)


class Watchlist(models.Model):
    """Stock watchlist for tracking without ownership"""
    symbol = models.CharField(max_length=20, unique=True)
    company_name = models.CharField(max_length=200, blank=True)
    added_at = models.DateTimeField(auto_now_add=True)
    target_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['symbol']

    def __str__(self):
        return self.symbol


class SIPPlan(models.Model):
    """Saved SIP calculation plans"""
    name = models.CharField(max_length=100)
    monthly_investment = models.DecimalField(max_digits=12, decimal_places=2)
    years = models.PositiveIntegerField()
    annual_return = models.DecimalField(max_digits=5, decimal_places=2)  # User must provide
    inflation_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    step_up_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    target_amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - ₹{self.monthly_investment}/month"


class StockAlert(models.Model):
    """Price alerts for stocks"""
    ALERT_TYPES = [
        ('above', 'Price Above'),
        ('below', 'Price Below'),
        ('change_pct', 'Change Percent'),
    ]

    symbol = models.CharField(max_length=20)
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPES)
    threshold = models.DecimalField(max_digits=12, decimal_places=2)
    is_active = models.BooleanField(default=True)
    triggered = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    triggered_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.symbol} - {self.get_alert_type_display()} ₹{self.threshold}"
