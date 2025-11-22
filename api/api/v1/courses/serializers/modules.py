"""
Module and Resource Serializers
"""

from rest_framework import serializers
from apps.courses.models import (
    PathModule,
    ModuleDetail,
    ModuleImage,
    Resource,
    ModuleToolOverride,
)


class ModuleImageSerializer(serializers.ModelSerializer):
    """Serializer for ModuleImage."""
    
    class Meta:
        model = ModuleImage
        fields = [
            'id',
            'title',
            'image',
            'alt_text',
            'order',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class ResourceSerializer(serializers.ModelSerializer):
    """Serializer for Resource with validation."""
    
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    
    class Meta:
        model = Resource
        fields = [
            'id',
            'module',
            'type',
            'type_display',
            'title',
            'description',
            'file',
            'url',
            'order',
            'is_required',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'type_display', 'created_at', 'updated_at']
    
    def validate(self, data):
        """Validate file/url consistency based on type."""
        resource_type = data.get('type')
        file_obj = data.get('file')
        url = data.get('url')
        
        # File types require file, not URL
        if resource_type in ['pdf', 'pptx', 'docx']:
            if not file_obj:
                raise serializers.ValidationError({
                    'file': 'File is required for this resource type'
                })
            if url:
                raise serializers.ValidationError({
                    'url': 'URL should not be set for file types'
                })
        
        # URL type requires URL, not file
        if resource_type == 'url':
            if not url:
                raise serializers.ValidationError({
                    'url': 'URL is required for external link type'
                })
            if file_obj:
                raise serializers.ValidationError({
                    'file': 'File should not be set for URL type'
                })
        
        return data


class ModuleDetailSerializer(serializers.ModelSerializer):
    """Serializer for ModuleDetail."""
    
    content_type_display = serializers.CharField(
        source='get_content_type_display',
        read_only=True
    )
    
    class Meta:
        model = ModuleDetail
        fields = [
            'id',
            'module',
            'content_type',
            'content_type_display',
            'text_content',
            'pdf_file',
            'objectives',
            'is_ai_generated',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class PathModuleSerializer(serializers.ModelSerializer):
    """List view for PathModule."""
    
    resources = ResourceSerializer(many=True, read_only=True)
    images = ModuleImageSerializer(many=True, read_only=True)
    detail = ModuleDetailSerializer(read_only=True)
    
    class Meta:
        model = PathModule
        fields = [
            'id',
            'path',
            'title',
            'slug',
            'category',
            'description',
            'outcomes',
            'order',
            'is_published',
            'published_at',
            'resources',
            'images',
            'detail',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'slug', 'published_at', 'created_at', 'updated_at']

class PathModuleListSerializer(serializers.ModelSerializer):
    """List view for PathModule."""
    
    resources = ResourceSerializer(many=True, read_only=True)
    images = ModuleImageSerializer(many=True, read_only=True)
    detail = ModuleDetailSerializer(read_only=True)
    
    class Meta:
        model = PathModule
        fields = [
            'id',
            'path',
            'title',
            'slug',
            'category',
            'description',
            'outcomes',
            'order',
            'is_published',
            'published_at',
            'resources',
            'images',
            'detail',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'slug', 'published_at', 'created_at', 'updated_at']


class PathModuleCreateUpdateSerializer(serializers.ModelSerializer):
    """Create/Update serializer for PathModule."""
    
    class Meta:
        model = PathModule
        fields = [
            'id',
            'path',
            'title',
            'category',
            'description',
            'outcomes',
            'order',
            'is_published',
        ]
        read_only_fields = ['id']
