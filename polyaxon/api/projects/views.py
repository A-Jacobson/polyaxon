from rest_framework.exceptions import ValidationError
from rest_framework.generics import CreateAPIView, ListAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated

import auditor

from api.projects import queries
from api.projects.serializers import (
    BookmarkedProjectSerializer,
    ProjectDetailSerializer,
    ProjectSerializer
)
from api.utils.views.auditor_mixin import AuditorMixinView
from db.models.projects import Project
from event_manager.events.project import (
    PROJECT_CREATED,
    PROJECT_DELETED_TRIGGERED,
    PROJECT_UPDATED,
    PROJECT_VIEWED
)
from libs.permissions.projects import IsProjectOwnerOrPublicReadOnly


class ProjectCreateView(CreateAPIView):
    """Create a project."""
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = (IsAuthenticated,)

    def perform_create(self, serializer):
        project = serializer.validated_data['name']
        user = self.request.user
        if self.queryset.filter(user=user, name=project).count() > 0:
            raise ValidationError('A project with name `{}` already exists.'.format(project))
        instance = serializer.save(user=user)
        auditor.record(event_type=PROJECT_CREATED, instance=instance)


class ProjectListView(ListAPIView):
    """List projects for a user."""
    queryset = queries.projects.order_by('-updated_at')
    serializer_class = BookmarkedProjectSerializer
    permission_classes = (IsAuthenticated,)

    def filter_queryset(self, queryset):
        username = self.kwargs['username']
        if self.request.user.is_staff or self.request.user.username == username:
            # User checking own projects
            return queryset.filter(user__username=username)

        # Use checking other user public projects
        return queryset.filter(user__username=username, is_public=True)


class ProjectDetailView(AuditorMixinView, RetrieveUpdateDestroyAPIView):
    """
    get:
        Get a project details.
    patch:
        Update a project details.
    delete:
        Delete a project.
    """
    queryset = queries.projects_details
    serializer_class = ProjectDetailSerializer
    permission_classes = (IsAuthenticated, IsProjectOwnerOrPublicReadOnly)
    lookup_field = 'name'
    get_event = PROJECT_VIEWED
    update_event = PROJECT_UPDATED
    delete_event = PROJECT_DELETED_TRIGGERED

    def filter_queryset(self, queryset):
        username = self.kwargs['username']
        return queryset.filter(user__username=username)
