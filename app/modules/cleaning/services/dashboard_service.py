"""
Xcleaners v3 — Dashboard Service.

Provides KPI summaries, revenue charts, team performance,
booking stats, client stats, and daily analytics aggregation
for the owner dashboard.

Tables: cleaning_bookings, cleaning_invoices, cleaning_teams,
        cleaning_clients, cleaning_daily_analytics, cleaning_job_logs.
"""

import logging
from datetime import date, datetime, timedelta
from typing import Optional

from app.database import Database

logger = logging.getLogger("xcleaners.dashboard_service")


# ============================================
# DASHBOARD SUMMARY (KPIs)
# ============================================

async def get_dashboard_summary(db: Database, business_id: str) -> dict:
    """
    Return top-level KPIs for the owner dashboard:
    - revenue_this_month
    - bookings_today (total, completed, in_progress)
    - active_clients
    - active_teams
    - overdue_invoices (count + total_amount)
    - unassigned_jobs (today)
    """
    today = date.today()
    month_start = today.replace(day=1)

    # Revenue this month (from completed bookings)
    revenue_row = await db.pool.fetchrow(
        """SELECT
            COALESCE(SUM(quoted_price), 0) AS revenue,
            COUNT(*) AS booking_count
           FROM cleaning_bookings
           WHERE business_id = $1
             AND scheduled_date >= $2
             AND scheduled_date <= $3
             AND status NOT IN ('cancelled', 'no_show')""",
        business_id, month_start, today,
    )

    # Last month revenue for comparison
    last_month_end = month_start - timedelta(days=1)
    last_month_start = last_month_end.replace(day=1)
    # Compare same number of days into last month
    last_month_compare_end = last_month_start + timedelta(days=today.day - 1)
    if last_month_compare_end > last_month_end:
        last_month_compare_end = last_month_end

    last_month_revenue = await db.pool.fetchval(
        """SELECT COALESCE(SUM(quoted_price), 0)
           FROM cleaning_bookings
           WHERE business_id = $1
             AND scheduled_date >= $2
             AND scheduled_date <= $3
             AND status NOT IN ('cancelled', 'no_show')""",
        business_id, last_month_start, last_month_compare_end,
    )

    # Bookings today
    today_row = await db.pool.fetchrow(
        """SELECT
            COUNT(*) AS total,
            COUNT(*) FILTER (WHERE status = 'completed') AS completed,
            COUNT(*) FILTER (WHERE status = 'in_progress') AS in_progress,
            COUNT(*) FILTER (WHERE team_id IS NULL AND status NOT IN ('cancelled', 'no_show')) AS unassigned
           FROM cleaning_bookings
           WHERE business_id = $1 AND scheduled_date = $2""",
        business_id, today,
    )

    # Active clients (have a booking in the last 90 days)
    active_clients = await db.pool.fetchval(
        """SELECT COUNT(DISTINCT client_id)
           FROM cleaning_bookings
           WHERE business_id = $1
             AND scheduled_date >= $2
             AND status NOT IN ('cancelled', 'no_show')""",
        business_id, today - timedelta(days=90),
    )

    # Active teams
    active_teams = await db.pool.fetchval(
        "SELECT COUNT(*) FROM cleaning_teams WHERE business_id = $1 AND is_active = true",
        business_id,
    )

    # Overdue invoices
    overdue_row = await db.pool.fetchrow(
        """SELECT
            COUNT(*) AS count,
            COALESCE(SUM(total - COALESCE(amount_paid, 0)), 0) AS total
           FROM cleaning_invoices
           WHERE business_id = $1
             AND status IN ('sent', 'overdue', 'partial')
             AND due_date < $2""",
        business_id, today,
    )

    revenue = float(revenue_row["revenue"])
    last_rev = float(last_month_revenue)
    pct_change = (
        round(((revenue - last_rev) / last_rev) * 100, 1)
        if last_rev > 0 else 0
    )

    return {
        "revenue_this_month": revenue,
        "revenue_change_pct": pct_change,
        "bookings_today": {
            "total": today_row["total"],
            "completed": today_row["completed"],
            "in_progress": today_row["in_progress"],
        },
        "active_clients": active_clients or 0,
        "active_teams": active_teams or 0,
        "overdue_invoices": {
            "count": overdue_row["count"],
            "total_amount": float(overdue_row["total"]),
        },
        "unassigned_jobs": today_row["unassigned"],
        "date": today.isoformat(),
    }


# ============================================
# REVENUE CHART
# ============================================

async def get_revenue_chart(
    db: Database,
    business_id: str,
    period: str = "month",
) -> dict:
    """
    Return revenue data points for charting.

    period: 'week' (last 7 days), 'month' (last 30 days), 'quarter' (last 90 days)
    """
    today = date.today()
    if period == "week":
        start = today - timedelta(days=6)
    elif period == "quarter":
        start = today - timedelta(days=89)
    else:
        start = today - timedelta(days=29)

    rows = await db.pool.fetch(
        """SELECT
            scheduled_date AS day,
            COALESCE(SUM(quoted_price) FILTER (WHERE status NOT IN ('cancelled', 'no_show')), 0) AS revenue,
            COUNT(*) FILTER (WHERE status NOT IN ('cancelled', 'no_show')) AS bookings
           FROM cleaning_bookings
           WHERE business_id = $1
             AND scheduled_date >= $2
             AND scheduled_date <= $3
           GROUP BY scheduled_date
           ORDER BY scheduled_date""",
        business_id, start, today,
    )

    # Fill in missing days with zeroes
    data_map = {str(r["day"]): {"revenue": float(r["revenue"]), "bookings": r["bookings"]} for r in rows}
    data_points = []
    current = start
    while current <= today:
        day_str = current.isoformat()
        entry = data_map.get(day_str, {"revenue": 0, "bookings": 0})
        data_points.append({
            "date": day_str,
            "revenue": entry["revenue"],
            "bookings": entry["bookings"],
        })
        current += timedelta(days=1)

    total = sum(d["revenue"] for d in data_points)
    return {
        "period": period,
        "start": start.isoformat(),
        "end": today.isoformat(),
        "total_revenue": total,
        "data": data_points,
    }


# ============================================
# TEAM PERFORMANCE
# ============================================

async def get_team_performance(db: Database, business_id: str) -> list:
    """
    Return performance stats per team:
    - jobs completed (today, this week)
    - total hours worked
    - average rating
    """
    today = date.today()
    week_start = today - timedelta(days=today.weekday())

    teams = await db.pool.fetch(
        "SELECT id, name, color FROM cleaning_teams WHERE business_id = $1 AND is_active = true ORDER BY name",
        business_id,
    )

    result = []
    for team in teams:
        team_id = str(team["id"])

        # Today's stats
        today_row = await db.pool.fetchrow(
            """SELECT
                COUNT(*) AS total_jobs,
                COUNT(*) FILTER (WHERE status = 'completed') AS completed,
                COUNT(*) FILTER (WHERE status = 'in_progress') AS in_progress,
                COALESCE(SUM(estimated_duration_minutes), 0) AS total_minutes
               FROM cleaning_bookings
               WHERE business_id = $1 AND team_id = $2 AND scheduled_date = $3
                 AND status NOT IN ('cancelled', 'no_show')""",
            business_id, team["id"], today,
        )

        # This week stats
        week_row = await db.pool.fetchrow(
            """SELECT
                COUNT(*) AS total_jobs,
                COUNT(*) FILTER (WHERE status = 'completed') AS completed,
                COALESCE(SUM(estimated_duration_minutes) FILTER (WHERE status = 'completed'), 0) AS completed_minutes,
                COALESCE(SUM(quoted_price) FILTER (WHERE status NOT IN ('cancelled', 'no_show')), 0) AS revenue
               FROM cleaning_bookings
               WHERE business_id = $1 AND team_id = $2
                 AND scheduled_date >= $3 AND scheduled_date <= $4
                 AND status NOT IN ('cancelled', 'no_show')""",
            business_id, team["id"], week_start, today,
        )

        # Average rating
        avg_rating = await db.pool.fetchval(
            """SELECT ROUND(AVG(r.rating), 1)
               FROM cleaning_reviews r
               JOIN cleaning_bookings b ON b.id = r.booking_id
               WHERE b.team_id = $1 AND b.business_id = $2""",
            team["id"], business_id,
        )

        result.append({
            "team_id": team_id,
            "team_name": team["name"],
            "team_color": team["color"],
            "today": {
                "total_jobs": today_row["total_jobs"],
                "completed": today_row["completed"],
                "in_progress": today_row["in_progress"],
                "total_hours": round(today_row["total_minutes"] / 60, 1),
            },
            "week": {
                "total_jobs": week_row["total_jobs"],
                "completed": week_row["completed"],
                "hours_worked": round(week_row["completed_minutes"] / 60, 1),
                "revenue": float(week_row["revenue"]),
            },
            "avg_rating": float(avg_rating) if avg_rating else None,
        })

    return result


# ============================================
# BOOKING STATS
# ============================================

async def get_booking_stats(db: Database, business_id: str) -> dict:
    """
    Return booking completion/cancellation/no-show rates
    for the last 30 days.
    """
    today = date.today()
    start = today - timedelta(days=29)

    row = await db.pool.fetchrow(
        """SELECT
            COUNT(*) AS total,
            COUNT(*) FILTER (WHERE status = 'completed') AS completed,
            COUNT(*) FILTER (WHERE status = 'cancelled') AS cancelled,
            COUNT(*) FILTER (WHERE status = 'no_show') AS no_show,
            COUNT(*) FILTER (WHERE status = 'rescheduled') AS rescheduled
           FROM cleaning_bookings
           WHERE business_id = $1
             AND scheduled_date >= $2
             AND scheduled_date <= $3""",
        business_id, start, today,
    )

    total = row["total"] or 1  # avoid division by zero
    return {
        "period_days": 30,
        "total": row["total"],
        "completed": row["completed"],
        "cancelled": row["cancelled"],
        "no_show": row["no_show"],
        "rescheduled": row["rescheduled"],
        "completion_rate": round(row["completed"] / total * 100, 1),
        "cancellation_rate": round(row["cancelled"] / total * 100, 1),
        "no_show_rate": round(row["no_show"] / total * 100, 1),
    }


# ============================================
# CLIENT STATS
# ============================================

async def get_client_stats(db: Database, business_id: str) -> dict:
    """
    Return client statistics:
    - new_clients (last 30 days)
    - total_clients
    - churn (inactive > 90 days)
    - top clients by LTV
    """
    today = date.today()

    total_clients = await db.pool.fetchval(
        "SELECT COUNT(*) FROM cleaning_clients WHERE business_id = $1 AND status = 'active'",
        business_id,
    )

    new_clients = await db.pool.fetchval(
        """SELECT COUNT(*) FROM cleaning_clients
           WHERE business_id = $1 AND created_at >= $2""",
        business_id, today - timedelta(days=30),
    )

    # Churn: clients with no booking in last 90 days who had a booking before
    churned = await db.pool.fetchval(
        """SELECT COUNT(DISTINCT c.id)
           FROM cleaning_clients c
           WHERE c.business_id = $1
             AND c.status = 'active'
             AND EXISTS (
                 SELECT 1 FROM cleaning_bookings b
                 WHERE b.client_id = c.id AND b.business_id = $1
                   AND b.scheduled_date < $2
                   AND b.status = 'completed'
             )
             AND NOT EXISTS (
                 SELECT 1 FROM cleaning_bookings b
                 WHERE b.client_id = c.id AND b.business_id = $1
                   AND b.scheduled_date >= $2
                   AND b.status NOT IN ('cancelled', 'no_show')
             )""",
        business_id, today - timedelta(days=90),
    )

    # Top 5 clients by LTV (total paid)
    top_clients = await db.pool.fetch(
        """SELECT
            c.id, c.first_name, c.last_name,
            COALESCE(SUM(i.amount_paid), 0) AS ltv,
            COUNT(DISTINCT b.id) AS total_bookings
           FROM cleaning_clients c
           LEFT JOIN cleaning_invoices i ON i.client_id = c.id AND i.business_id = $1
           LEFT JOIN cleaning_bookings b ON b.client_id = c.id AND b.business_id = $1 AND b.status = 'completed'
           WHERE c.business_id = $1 AND c.status = 'active'
           GROUP BY c.id, c.first_name, c.last_name
           ORDER BY ltv DESC
           LIMIT 5""",
        business_id,
    )

    return {
        "total_clients": total_clients or 0,
        "new_clients_30d": new_clients or 0,
        "churned_clients": churned or 0,
        "top_clients": [
            {
                "id": str(r["id"]),
                "name": f"{r['first_name'] or ''} {r['last_name'] or ''}".strip(),
                "ltv": float(r["ltv"]),
                "total_bookings": r["total_bookings"],
            }
            for r in top_clients
        ],
    }


# ============================================
# AGGREGATE DAILY ANALYTICS
# ============================================

async def aggregate_daily_analytics(
    db: Database,
    business_id: str,
    target_date: Optional[date] = None,
) -> dict:
    """
    Populate the cleaning_daily_analytics table for a given date.
    Upserts (INSERT ... ON CONFLICT UPDATE).
    """
    if target_date is None:
        target_date = date.today()

    # Booking stats
    booking_row = await db.pool.fetchrow(
        """SELECT
            COUNT(*) AS total,
            COUNT(*) FILTER (WHERE status = 'completed') AS completed,
            COUNT(*) FILTER (WHERE status = 'cancelled') AS cancelled,
            COALESCE(SUM(quoted_price) FILTER (WHERE status = 'completed'), 0) AS revenue
           FROM cleaning_bookings
           WHERE business_id = $1 AND scheduled_date = $2""",
        business_id, target_date,
    )

    # Lead stats
    lead_row = await db.pool.fetchrow(
        """SELECT
            COUNT(*) AS new_leads,
            COUNT(*) FILTER (WHERE status = 'converted') AS converted
           FROM cleaning_leads
           WHERE business_id = $1 AND DATE(created_at) = $2""",
        business_id, target_date,
    )

    # New clients
    new_clients = await db.pool.fetchval(
        """SELECT COUNT(*) FROM cleaning_clients
           WHERE business_id = $1 AND DATE(created_at) = $2""",
        business_id, target_date,
    )

    # SMS stats
    sms_row = await db.pool.fetchrow(
        """SELECT
            COUNT(*) AS sms_sent,
            COALESCE(SUM(cost), 0) AS sms_cost
           FROM cleaning_notifications
           WHERE business_id = $1 AND channel = 'sms' AND DATE(created_at) = $2""",
        business_id, target_date,
    )

    # Upsert
    await db.pool.execute(
        """INSERT INTO cleaning_daily_analytics
           (business_id, date, total_bookings, completed_bookings, cancelled_bookings,
            revenue, new_leads, converted_leads, new_clients, sms_sent, sms_cost)
           VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
           ON CONFLICT (business_id, date) DO UPDATE SET
            total_bookings = EXCLUDED.total_bookings,
            completed_bookings = EXCLUDED.completed_bookings,
            cancelled_bookings = EXCLUDED.cancelled_bookings,
            revenue = EXCLUDED.revenue,
            new_leads = EXCLUDED.new_leads,
            converted_leads = EXCLUDED.converted_leads,
            new_clients = EXCLUDED.new_clients,
            sms_sent = EXCLUDED.sms_sent,
            sms_cost = EXCLUDED.sms_cost,
            updated_at = NOW()""",
        business_id, target_date,
        booking_row["total"], booking_row["completed"], booking_row["cancelled"],
        booking_row["revenue"],
        lead_row["new_leads"], lead_row["converted"],
        new_clients or 0,
        sms_row["sms_sent"], sms_row["sms_cost"],
    )

    return {
        "date": target_date.isoformat(),
        "total_bookings": booking_row["total"],
        "completed_bookings": booking_row["completed"],
        "cancelled_bookings": booking_row["cancelled"],
        "revenue": float(booking_row["revenue"]),
        "new_leads": lead_row["new_leads"],
        "new_clients": new_clients or 0,
    }
