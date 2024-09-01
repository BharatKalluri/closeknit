from django.contrib.auth.models import User
from django.db.models import QuerySet
from datetime import datetime

from backend.models import Subscription, Community, Item, Lease, Invite


def get_user(user_name: str) -> User | None:
    try:
        return User.objects.get(username=user_name)
    except User.DoesNotExist:
        return None


def get_all_users_from_communities_the_user_belongs_to(user: User) -> list[User]:
    communities_the_user_belongs_to = Community.objects.filter(members=user)
    return list(
        User.objects.filter(communities__in=communities_the_user_belongs_to).distinct()
    )


def get_items_available_for_lease(user: User) -> QuerySet[Item]:
    all_users_of_communities_the_user_belongs_to = (
        get_all_users_from_communities_the_user_belongs_to(user)
    )
    all_items = Item.objects.filter(
        owner__in=all_users_of_communities_the_user_belongs_to, is_active=True
    )
    items_already_leased_out = Lease.objects.filter(
        end_date__gt=datetime.now(),
        item__in=all_items,
    )
    return all_items.exclude(owner=user).exclude(
        pk__in=[lease.item.pk for lease in items_already_leased_out]
    )


def get_subscriptions_available_for_share(user: User) -> QuerySet[Subscription]:
    all_users_of_communities_the_user_belongs_to = (
        get_all_users_from_communities_the_user_belongs_to(user)
    )
    all_subscriptions = Subscription.objects.filter(
        owner__in=all_users_of_communities_the_user_belongs_to
    )
    return all_subscriptions.exclude(owner=user).exclude(shared_to=user)


def get_dashboard_data(user: User) -> dict:
    users_in_communities = get_all_users_from_communities_the_user_belongs_to(user)
    your_items_count = Item.objects.filter(owner=user).count()
    your_subscriptions_count = Subscription.objects.filter(owner=user).count()
    items_available_for_lease = get_items_available_for_lease(user).count()
    subscriptions_available_for_share = get_subscriptions_available_for_share(
        user=user
    ).count()
    total_active_members_across_communities = len(users_in_communities)
    total_communities_user_belongs_to = Community.objects.filter(members=user).count()

    return {
        "your_items_count": your_items_count,
        "your_subscriptions_count": your_subscriptions_count,
        "total_shared_items": your_items_count + your_subscriptions_count,
        "items_available_for_lease": items_available_for_lease,
        "subscriptions_available_for_share": subscriptions_available_for_share,
        "total_available_items": items_available_for_lease
        + subscriptions_available_for_share,
        "total_communities_user_belongs_to": total_communities_user_belongs_to,
        "total_active_members_across_communities": total_active_members_across_communities,
    }


def get_user_subscriptions(user: User) -> dict:
    return {
        "owned": Subscription.objects.filter(owner=user),
        "shared": Subscription.objects.filter(shared_to=user),
    }


def get_discover_data(user: User) -> dict:
    return {
        "subscriptions": get_subscriptions_available_for_share(user),
        "items": get_items_available_for_lease(user),
    }


def get_user_communities(user: User) -> dict:
    return {
        "owned": Community.objects.filter(owner=user),
        "shared": Community.objects.filter(members=user),
    }


def get_user_items(user: User) -> dict:
    return {
        "owned": Item.objects.filter(owner=user),
        "leased": Lease.objects.filter(lessee=user),
        "leased_out": Lease.objects.filter(item__owner=user),
    }


def add_user_to_community(community: Community, user: User) -> None:
    if not community.members.filter(username=user.username).exists():
        community.members.add(user)
        community.save()


def create_invite(community: Community, created_by: User) -> Invite:
    return Invite.objects.create(community=community, created_by=created_by)


def use_invite(invite: Invite, user: User) -> bool:
    if invite.use_invite(user):
        invite.community.members.add(user)
        return True
    return False