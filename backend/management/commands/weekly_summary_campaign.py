import json

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.conf import settings
from django.core.mail import send_mail

from backend.services import (
    get_subscriptions_available_for_share,
    get_items_available_for_lease,
)


def format_email_content(shared_items, shared_subscriptions):
    closeknit_link = '<a href="https://closeknit.io">Closeknit</a>'
    content = f" We're thrilled to share some exciting updates from your {closeknit_link} community!<br><br>"

    if shared_items:
        content += "📢 What's in the Sharing Pool:<br>"
        for item in shared_items:
            content += f"- {item.name} (shared by {item.owner.username})<br>"
        content += "<br>"

    if shared_subscriptions:
        content += "📢 Subscriptions available for sharing:<br>"
        for subscription in shared_subscriptions:
            content += (
                f"- {subscription.name} (shared by {subscription.owner.username})<br>"
            )

    content += """
<br><br>🤝 Remember, sharing is caring! Feel free to reach out to bharat or any other community members if you'd like to borrow these items. It's a great way to connect with your neighbors and make the most of our shared resources.

<br><br>Have something interesting to share with the community? We'd love to see what you can add to our growing pool of shared treasures!

<br><br>🔍 Curious to learn more? Visit our Closeknit website to discover all the amazing resources available in your community.

<br><br>Stay connected, stay sharing, and enjoy the power of community!    
    """
    return content


class Command(BaseCommand):
    help = "Send weekly email to users about items and subscriptions shared with them"

    def handle(self, *args, **options):
        users = User.objects.all()

        for user in users:
            # Fetch items shared with the user in the last 7 days
            shared_items = get_items_available_for_lease(user)

            # Fetch subscriptions shared with the user in the last 7 days
            shared_subscriptions = get_subscriptions_available_for_share(user)

            if shared_items or shared_subscriptions:
                self.send_email(user, shared_items, shared_subscriptions)

    def send_email(self, user, shared_items, shared_subscriptions):
        subject = "Exciting Updates from Your Closeknit Community! 🎉"
        message = format_email_content(shared_items, shared_subscriptions)
        from_email = settings.DEFAULT_FROM_EMAIL
        recipient_list = [user.email]

        print(
            json.dumps(
                dict(
                    subject=subject,
                    message=message,
                    from_email=from_email,
                    recipient_list=recipient_list,
                ),
                indent=4,
            )
        )
        send_mail(
            subject=subject,
            from_email=from_email,
            recipient_list=recipient_list,
            html_message=message,
            message="",
        )
        self.stdout.write(self.style.SUCCESS(f"Email sent to {recipient_list}"))
