"""
Custom Admin Site for PrintDuka with Dashboard functionality
"""
from django.contrib.admin import AdminSite
from django.utils import timezone
import json


class PrintDukaAdminSite(AdminSite):
    """Custom Admin Site with Enhanced Dashboard"""
    site_header = "PrintDuka Administration"
    site_title = "PrintDuka Admin"
    index_title = "Dashboard Overview"
    
    # Use separate dashboard template
    index_template = "admin/dashboard.html"
    
    def index(self, request, extra_context=None):
        """
        Custom admin index page with dashboard widgets
        """
        from .admin_dashboard import (
            get_dashboard_stats,
            get_order_status_distribution,
            get_sales_performance_trend,
            get_recent_orders,
            get_active_alerts,
            get_user_activity_logs,
            get_top_selling_products,
            get_profit_margin_data,
            get_outstanding_receivables,
            get_recent_payments,
            get_payment_collection_rate,
            get_staff_performance,
            get_time_based_insights
        )

        extra_context = extra_context or {}

        try:
            # Dashboard metrics
            dashboard_stats = get_dashboard_stats()
            order_distribution = get_order_status_distribution()
            sales_trend = get_sales_performance_trend(months=6)
            recent_orders = get_recent_orders(limit=5)

            # Alerts & activity
            active_alerts = get_active_alerts(limit=5)
            recent_activity = get_user_activity_logs(limit=10)
            top_products = get_top_selling_products(limit=5)
            profit_margins = get_profit_margin_data()

            # Financial, Staff & Time-based insights
            receivables = get_outstanding_receivables()
            recent_payments = get_recent_payments(limit=5)
            collection_rate = get_payment_collection_rate()
            staff_performance = get_staff_performance()
            time_insights = get_time_based_insights()

            # Add data to context
            extra_context.update({
                'dashboard_stats': dashboard_stats,
                'order_distribution': json.dumps(order_distribution),
                'sales_trend': json.dumps(sales_trend, default=str),
                'recent_orders': recent_orders,
                'active_alerts': active_alerts,
                'recent_activity': recent_activity,
                'top_products': top_products,
                'profit_margins': profit_margins,
                'receivables': receivables,
                'recent_payments': recent_payments,
                'collection_rate': collection_rate,
                'staff_performance': staff_performance,
                'time_insights': time_insights,
            })

        except Exception as e:
            # Do not break admin if dashboard fails
            print(f"Dashboard error: {e}")
            import traceback
            traceback.print_exc()

            extra_context.update({
                'dashboard_stats': {},
                'order_distribution': json.dumps([]),
                'sales_trend': json.dumps([]),
                'recent_orders': [],
                'active_alerts': [],
                'recent_activity': [],
                'top_products': [],
                'profit_margins': {},
                'receivables': {},
                'recent_payments': [],
                'collection_rate': {},
                'staff_performance': {},
                'time_insights': {},
            })

        return super().index(request, extra_context)
