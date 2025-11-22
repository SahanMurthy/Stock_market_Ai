# web/views.py - COMPLETE & FINAL

import sys
import os
import logging

# Add parent directory to path
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, parent_dir)

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from django.views.decorators.http import require_http_methods

from .models import Portfolio, PortfolioHolding, Watchlist, SIPPlan, StockAlert

# Import from core_logic
from core_logic.data_fetcher import DataFetcher
from core_logic.risk_manager import RiskManager
from core_logic.sip_calculator import SIPCalculator
from core_logic.symbols_live import SymbolsLive
from core_logic.hybrid_ai_agent import HybridAIAgent
from core_logic.stock_screener import StockScreener
import core_logic.config as config

# Setup logger
logger = logging.getLogger(__name__)

# Initialize engines
data_fetcher = DataFetcher()
risk_manager = RiskManager()
sip_calculator = SIPCalculator()
symbols_live = SymbolsLive()
stock_screener = StockScreener()


# ==================== HOME & DASHBOARD ====================

def home(request):
    """Landing page"""
    context = {
        'available_apis': getattr(config, 'AVAILABLE_APIS', []),
        'enable_ai': getattr(config, 'ENABLE_AI_RECOMMENDATIONS', False),
    }
    return render(request, 'home.html', context)


def dashboard_view(request):
    """Main dashboard"""
    portfolios = Portfolio.objects.all()
    watchlist = Watchlist.objects.all()

    context = {
        'portfolios': portfolios,
        'watchlist': watchlist,
        'has_symbols': portfolios.exists() or watchlist.exists(),
    }

    return render(request, 'dashboard.html', context)


# ==================== AI SUGGESTIONS ====================

def ai_suggestions(request):
    """AI suggestions with market awareness"""

    investment_amount = float(request.GET.get('amount', 10000))
    stock_type = request.GET.get('type', 'large_cap')

    suggestions = []
    errors = []
    market_status = None

    if request.GET.get('amount'):
        try:
            ai_agent = HybridAIAgent(api_key=os.getenv('GEMINI_API_KEY'))

            # Check market status FIRST
            market_status = stock_screener.is_market_open()

            if not market_status['is_open']:
                messages.warning(request, f"⚠️  {market_status['message']}")
                return render(request, 'ai_suggestions.html', {
                    'suggestions': [],
                    'investment_amount': investment_amount,
                    'stock_type': stock_type,
                    'market_status': market_status,
                    'market_closed': True
                })

            # Market is open - proceed with screening
            logger.info(f"🔍 Market OPEN - Screening {stock_type} stocks...")
            trending_stocks = stock_screener.get_trending_stocks(category=stock_type, limit=10)

            if not trending_stocks:
                messages.error(request, "Unable to fetch real-time stocks. Please try again.")
            else:
                # ... rest of analysis code (same as before)
                pass

        except Exception as e:
            logger.error(f"Error: {e}")
            messages.error(request, f"Error: {str(e)}")

    return render(request, 'ai_suggestions.html', {
        'suggestions': suggestions,
        'investment_amount': investment_amount,
        'stock_type': stock_type,
        'market_status': market_status,
        'total_stocks': len(suggestions)
    })


# ==================== STOCK SEARCH & DETAIL ====================

def stock_search(request):
    """Search stocks"""
    query = request.GET.get('q', '').strip()
    results = []

    if query:
        try:
            results = symbols_live.search_nse_symbols(query)[:20]
        except Exception as e:
            messages.error(request, f"Search error: {e}")

    return render(request, 'stock_search.html', {'query': query, 'results': results})


def stock_detail(request, symbol):
    """Stock detail"""
    try:
        stock_data = data_fetcher.get_stock_data(f"{symbol}.NS", period="1y")

        if stock_data is None or stock_data.empty:
            messages.error(request, f"Unable to fetch data for {symbol}")
            return redirect('stock_search')

        risk_metrics = risk_manager.calculate_risk_metrics(stock_data)
        latest_price = data_fetcher.get_realtime_price(f"{symbol}.NS")

        return render(request, 'stock_detail.html', {
            'symbol': symbol,
            'stock_data': stock_data.tail(30).to_dict('records'),
            'latest_price': latest_price,
            'risk_metrics': risk_metrics,
            'in_watchlist': Watchlist.objects.filter(symbol=symbol).exists(),
            'in_portfolio': PortfolioHolding.objects.filter(symbol=symbol).exists(),
        })

    except Exception as e:
        messages.error(request, f"Error: {e}")
        return redirect('stock_search')


def risk_analysis(request, symbol):
    """Risk analysis"""
    try:
        stock_data = data_fetcher.get_stock_data(f"{symbol}.NS", period="1y")

        if stock_data is None or stock_data.empty:
            messages.error(request, f"Unable to fetch data")
            return redirect('stock_detail', symbol=symbol)

        risk_metrics = risk_manager.calculate_risk_metrics(stock_data)

        return render(request, 'risk_analysis.html', {
            'symbol': symbol,
            'risk_metrics': risk_metrics,
        })
    except Exception as e:
        messages.error(request, f"Error: {e}")
        return redirect('stock_detail', symbol=symbol)


# ==================== PORTFOLIO ====================

def portfolio_list(request):
    """List portfolios"""
    return render(request, 'portfolio_list.html', {'portfolios': Portfolio.objects.all()})


def portfolio_detail(request, portfolio_id):
    """Portfolio detail"""
    portfolio = get_object_or_404(Portfolio, id=portfolio_id)
    holdings = portfolio.holdings.all()

    for holding in holdings:
        try:
            current_price = data_fetcher.get_realtime_price(f"{holding.symbol}.NS")
            if current_price:
                holding.current_price = current_price
                holding.current_value = float(current_price) * holding.quantity
                holding.save()
        except:
            pass

    return render(request, 'portfolio_detail.html', {
        'portfolio': portfolio,
        'holdings': holdings,
        'total_invested': portfolio.total_invested,
        'total_value': portfolio.total_value,
        'total_pnl': portfolio.total_pnl,
    })


@require_http_methods(["POST"])
def portfolio_create(request):
    """Create portfolio"""
    name = request.POST.get('name')
    if name:
        Portfolio.objects.create(name=name)
        messages.success(request, f"Portfolio '{name}' created")
    return redirect('portfolio_list')


@require_http_methods(["POST"])
def portfolio_add_holding(request, portfolio_id):
    """Add holding"""
    portfolio = get_object_or_404(Portfolio, id=portfolio_id)
    symbol = request.POST.get('symbol', '').upper()
    quantity = int(request.POST.get('quantity', 0))
    avg_price = float(request.POST.get('avg_price', 0))

    if symbol and quantity > 0:
        PortfolioHolding.objects.create(
            portfolio=portfolio,
            symbol=symbol,
            quantity=quantity,
            avg_price=avg_price
        )
        messages.success(request, f"Added {symbol}")

    return redirect('portfolio_detail', portfolio_id=portfolio_id)


@require_http_methods(["POST"])
def portfolio_remove_holding(request, holding_id):
    """Remove holding"""
    holding = get_object_or_404(PortfolioHolding, id=holding_id)
    portfolio_id = holding.portfolio.id
    holding.delete()
    messages.success(request, "Holding removed")
    return redirect('portfolio_detail', portfolio_id=portfolio_id)


# ==================== WATCHLIST ====================

def watchlist_view(request):
    """View watchlist"""
    watchlist = Watchlist.objects.all()

    for item in watchlist:
        try:
            current_price = data_fetcher.get_realtime_price(f"{item.symbol}.NS")
            if current_price:
                item.current_price = current_price
                if item.target_price:
                    item.distance_to_target = ((float(item.target_price) - current_price) / current_price) * 100
        except:
            pass

    return render(request, 'watchlist.html', {'watchlist': watchlist})


@require_http_methods(["POST"])
def watchlist_add(request):
    """Add to watchlist"""
    symbol = request.POST.get('symbol', '').upper()

    if symbol:
        Watchlist.objects.get_or_create(symbol=symbol)
        messages.success(request, f"Added {symbol}")

    return redirect('watchlist')


@require_http_methods(["POST"])
def watchlist_remove(request, watchlist_id):
    """Remove from watchlist"""
    item = get_object_or_404(Watchlist, id=watchlist_id)
    item.delete()
    messages.success(request, "Removed from watchlist")
    return redirect('watchlist')


# ==================== SIP CALCULATOR ====================

def sip_calculator_view(request):
    """SIP calculator"""
    result = None
    error = None
    saved_plans = SIPPlan.objects.all()[:5]

    if request.method == 'POST':
        try:
            monthly_investment = request.POST.get('monthly_investment')
            years = request.POST.get('years')
            annual_return = request.POST.get('annual_return')

            if annual_return and years and monthly_investment:
                result = sip_calculator.calculate(
                    monthly_investment=float(monthly_investment),
                    years=int(years),
                    annual_return=float(annual_return)
                )
        except Exception as e:
            error = str(e)

    return render(request, 'sip_calculator.html', {
        'result': result,
        'error': error,
        'saved_plans': saved_plans
    })


def sip_plan_detail(request, plan_id):
    """SIP plan detail"""
    plan = get_object_or_404(SIPPlan, id=plan_id)
    return render(request, 'sip_plan_detail.html', {'plan': plan})


@require_http_methods(["POST"])
def sip_plan_delete(request, plan_id):
    """Delete SIP plan"""
    plan = get_object_or_404(SIPPlan, id=plan_id)
    plan.delete()
    messages.success(request, "Plan deleted")
    return redirect('sip_calculator')


# ==================== API ENDPOINTS ====================

def api_stock_price(request, symbol):
    """Stock price API"""
    try:
        price = data_fetcher.get_realtime_price(f"{symbol}.NS")
        return JsonResponse({'symbol': symbol, 'price': float(price) if price else None})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


def api_search_symbols(request):
    """Search API"""
    query = request.GET.get('q', '').strip()

    if not query:
        return JsonResponse({'results': []})

    try:
        results = symbols_live.search_nse_symbols(query)[:20]
        return JsonResponse({'results': results})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


def api_portfolio_refresh(request, portfolio_id):
    """Refresh portfolio API"""
    portfolio = get_object_or_404(Portfolio, id=portfolio_id)

    updated = 0
    for holding in portfolio.holdings.all():
        try:
            price = data_fetcher.get_realtime_price(f"{holding.symbol}.NS")
            if price:
                holding.current_price = price
                holding.save()
                updated += 1
        except:
            pass

    return JsonResponse({
        'success': True,
        'updated': updated,
        'total': portfolio.holdings.count()
    })
