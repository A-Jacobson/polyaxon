from django.urls import re_path
from rest_framework.urlpatterns import format_suffix_patterns

from api.bookmarks import views as bookmark_views
from api.jobs import views
from constants.urls import ID_PATTERN, JOB_ID_PATTERN, NAME_PATTERN, USERNAME_PATTERN, UUID_PATTERN

jobs_urlpatterns = [
    re_path(r'^{}/{}/jobs/{}/?$'.format(
        USERNAME_PATTERN, NAME_PATTERN, ID_PATTERN),
        views.JobDetailView.as_view()),
    re_path(r'^{}/{}/jobs/{}/restart/?$'.format(
        USERNAME_PATTERN, NAME_PATTERN, ID_PATTERN),
        views.JobRestartView.as_view()),
    re_path(r'^{}/{}/jobs/{}/statuses/?$'.format(
        USERNAME_PATTERN, NAME_PATTERN, JOB_ID_PATTERN),
        views.JobStatusListView.as_view()),
    re_path(r'^{}/{}/jobs/{}/statuses/{}/?$'.format(
        USERNAME_PATTERN, NAME_PATTERN, JOB_ID_PATTERN, UUID_PATTERN),
        views.JobStatusDetailView.as_view()),
    re_path(r'^{}/{}/jobs/{}/logs/?$'.format(
        USERNAME_PATTERN, NAME_PATTERN, JOB_ID_PATTERN),
        views.JobLogsView.as_view()),
    re_path(r'^{}/{}/jobs/{}/stop/?$'.format(
        USERNAME_PATTERN, NAME_PATTERN, ID_PATTERN),
        views.JobStopView.as_view()),
    re_path(r'^{}/{}/jobs/{}/outputs/download/?$'.format(
        USERNAME_PATTERN, NAME_PATTERN, ID_PATTERN),
        views.JobDownloadOutputsView.as_view()),
    re_path(r'^{}/{}/jobs/{}/outputs/tree/?$'.format(
        USERNAME_PATTERN, NAME_PATTERN, JOB_ID_PATTERN),
        views.JobOutputsTreeView.as_view()),
    re_path(r'^{}/{}/jobs/{}/outputs/files/?$'.format(
        USERNAME_PATTERN, NAME_PATTERN, JOB_ID_PATTERN),
        views.JobOutputsFilesView.as_view()),
    re_path(r'^{}/{}/jobs/{}/_heartbeat/?$'.format(
        USERNAME_PATTERN, NAME_PATTERN, ID_PATTERN),
        views.JobHeartBeatView.as_view()),
    re_path(r'^{}/{}/jobs/{}/bookmark/?$'.format(
        USERNAME_PATTERN, NAME_PATTERN, ID_PATTERN),
        bookmark_views.JobBookmarkCreateView.as_view()),
    re_path(r'^{}/{}/jobs/{}/unbookmark/?$'.format(
        USERNAME_PATTERN, NAME_PATTERN, ID_PATTERN),
        bookmark_views.JobBookmarkDeleteView.as_view()),
]

urlpatterns = format_suffix_patterns(jobs_urlpatterns)
