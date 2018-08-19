from rest_framework import fields, serializers

from db.models.bookmarks import Bookmark
from db.models.build_jobs import BuildJob, BuildJobStatus
from libs.spec_validation import validate_build_spec_config


class BuildJobStatusSerializer(serializers.ModelSerializer):
    uuid = fields.UUIDField(format='hex', read_only=True)

    class Meta:
        model = BuildJobStatus
        extra_kwargs = {'job': {'read_only': True}}
        exclude = []


class BuildJobSerializer(serializers.ModelSerializer):
    uuid = fields.UUIDField(format='hex', read_only=True)
    user = fields.SerializerMethodField()
    project = fields.SerializerMethodField()
    started_at = fields.DateTimeField(read_only=True)
    finished_at = fields.DateTimeField(read_only=True)

    class Meta:
        model = BuildJob
        fields = (
            'id',
            'uuid',
            'name',
            'unique_name',
            'user',
            'description',
            'created_at',
            'updated_at',
            'started_at',
            'finished_at',
            'last_status',
            'tags',
            'project',
        )

    def get_user(self, obj):
        return obj.user.username

    def get_project(self, obj):
        return obj.project.unique_name


class BuildJobDetailSerializer(BuildJobSerializer):
    resources = fields.SerializerMethodField()
    num_jobs = fields.SerializerMethodField()
    num_experiments = fields.SerializerMethodField()
    commit = fields.SerializerMethodField()
    bookmarked = fields.SerializerMethodField()

    class Meta(BuildJobSerializer.Meta):
        fields = BuildJobSerializer.Meta.fields + (
            'description',
            'config',
            'resources',
            'node_scheduled',
            'num_jobs',
            'num_experiments',
            'dockerfile',
            'commit',
            'bookmarked'
        )

    def get_commit(self, obj):
        return obj.code_reference.commit if obj.code_reference else None

    def get_resources(self, obj):
        return obj.resources.to_dict() if obj.resources else None

    def get_num_jobs(self, obj):
        return obj.jobs__count

    def get_num_experiments(self, obj):
        return obj.experiments__count

    def get_bookmarked(self, obj):
        return Bookmark.objects.filter(
            content_type__model='buildjob',
            object_id=obj.id,
            enabled=True).exists()


class BuildJobCreateSerializer(serializers.ModelSerializer):
    user = fields.SerializerMethodField()

    class Meta:
        model = BuildJob
        fields = ('id', 'user', 'name', 'description', 'config', 'tags')

    def get_user(self, obj):
        return obj.user.username

    def validate_config(self, config):
        """We only validate the config if passed.

        Also we use the BuildSpecification to check if this config was
        intended as job.
        """
        validate_build_spec_config(config)
        return config
