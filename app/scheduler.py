"""Background scheduler for automated tasks."""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timedelta
from app import db
from app.models import Event
from app.services import NotificationService


def init_scheduler(app):
    """Initialize the background scheduler.

    Args:
        app: Flask application instance
    """
    scheduler = BackgroundScheduler()

    # Run daily at configured hour to check for reminders
    reminder_hour = app.config.get("REMINDER_CHECK_HOUR", 9)

    @scheduler.scheduled_job(CronTrigger(hour=reminder_hour, minute=0))
    def check_and_send_reminders():
        """Check for events needing reminders and send them."""
        with app.app_context():
            today = datetime.now().date()

            # Find events with RSVP deadline in 7 days
            rsvp_reminder_date = today + timedelta(days=7)
            events_needing_rsvp_reminder = Event.query.filter(
                db.func.date(Event.rsvp_deadline) == rsvp_reminder_date,
                Event.status == "published",
            ).all()

            for event in events_needing_rsvp_reminder:
                app.logger.info(f"Sending RSVP reminders for event: {event.title}")
                NotificationService.send_rsvp_reminders(event)

            # Find events happening in 3 days (potluck reminder)
            potluck_reminder_date = today + timedelta(days=3)
            events_needing_potluck_reminder = Event.query.filter(
                db.func.date(Event.event_date) == potluck_reminder_date,
                Event.status == "published",
            ).all()

            for event in events_needing_potluck_reminder:
                app.logger.info(f"Sending potluck reminders for event: {event.title}")
                NotificationService.send_potluck_reminders(event)

            # Archive past events
            past_events = Event.query.filter(
                Event.event_date < datetime.now(), Event.status == "published"
            ).all()

            for event in past_events:
                app.logger.info(f"Archiving past event: {event.title}")
                event.status = "archived"

            if past_events:
                db.session.commit()

    scheduler.start()
    app.logger.info("Background scheduler started")

    # Store scheduler in app for cleanup
    app.scheduler = scheduler

