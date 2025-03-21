# roles/migrations/xxxx_create_initial_permissions.py

from django.db import migrations

def create_permissions(apps, schema_editor):
    """Create initial permissions"""
    Permission = apps.get_model('roles', 'Permission')
    
    # Define the permissions
    permissions = [
        {
            'code': 'create_tasks',
            'name': 'Create Tasks',
            'description': 'Can create new tasks in the system'
        },
        {
            'code': 'view_tasks',
            'name': 'View Tasks',
            'description': 'Can view tasks assigned to them or their team'
        },
        {
            'code': 'assign_tasks',
            'name': 'Assign Tasks',
            'description': 'Can assign tasks to other team members'
        },
        {
            'code': 'update_tasks',
            'name': 'Update Tasks',
            'description': 'Can update task details and progress'
        },
        {
            'code': 'delete_tasks',
            'name': 'Delete Tasks',
            'description': 'Can permanently delete tasks'
        },
        {
            'code': 'approve_tasks',
            'name': 'Approve Tasks',
            'description': 'Can review and approve completed tasks'
        },
        {
            'code': 'reject_tasks',
            'name': 'Reject Tasks',
            'description': 'Can reject tasks and request changes'
        },
        {
            'code': 'comment',
            'name': 'Comment',
            'description': 'Can leave comments on tasks'
        },
        {
            'code': 'view_reports',
            'name': 'View Reports',
            'description': 'Can access analytics and reporting'
        },
        {
            'code': 'manage_users',
            'name': 'Manage Users',
            'description': 'Can add, edit, and remove users'
        },
        {
            'code': 'manage_roles',
            'name': 'Manage Roles',
            'description': 'Can create and modify roles and permissions'
        },
    ]
    
    # Create the permissions
    for permission_data in permissions:
        Permission.objects.create(**permission_data)


def delete_permissions(apps, schema_editor):
    """Delete all permissions (for rollback)"""
    Permission = apps.get_model('roles', 'Permission')
    Permission.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('roles', '0001_initial'),  # Make sure this matches your latest migration
    ]

    operations = [
        migrations.RunPython(create_permissions, delete_permissions),
    ]