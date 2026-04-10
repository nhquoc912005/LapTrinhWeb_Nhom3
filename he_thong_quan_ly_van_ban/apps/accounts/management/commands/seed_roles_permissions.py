from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from ...role_groups import ensure_role_groups, get_role_permissions, sync_user_role_group


class Command(BaseCommand):
    help = "Tao group va gan quyen cho he thong"

    def handle(self, *args, **options):
        User = get_user_model()
        role_permissions = get_role_permissions(User)
        role_groups = ensure_role_groups(User)

        for role_name in role_permissions:
            group = role_groups[role_name]
            self.stdout.write(
                self.style.SUCCESS(
                    f"Da tao/cap nhat group '{role_name}' voi {group.permissions.count()} quyen."
                )
            )

        for user in User.objects.all():
            target_group = sync_user_role_group(user, role_groups=role_groups)
            if target_group:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Da gan user '{user.username}' vao group '{target_group.name}'."
                    )
                )

        self.stdout.write(self.style.SUCCESS("Hoan tat seed group va quyen."))
