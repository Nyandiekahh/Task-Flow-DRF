from django.db import models
from django.conf import settings
from organizations.models import Organization, TeamMember


class Task(models.Model):
    """Model for storing task information"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    CATEGORY_CHOICES = [
        ('general', 'General'),
        ('admin', 'Administrative'),
        ('finance', 'Finance'),
        ('hr', 'Human Resources'),
        ('marketing', 'Marketing'),
        ('operations', 'Operations'),
        ('planning', 'Planning'),
        ('research', 'Research'),
        ('sales', 'Sales'),
        ('other', 'Other'),
    ]
    
    VISIBILITY_CHOICES = [
        ('team', 'Team'),
        ('private', 'Private'),
        ('public', 'Public'),
    ]
    
    RECURRING_FREQUENCY_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('biweekly', 'Bi-weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
    ]
    
    # Basic task information
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='general')
    
    # Timeline
    start_date = models.DateTimeField(null=True, blank=True)
    due_date = models.DateTimeField(null=True, blank=True)
    estimated_hours = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    
    # Recurring task settings
    is_recurring = models.BooleanField(default=False)
    recurring_frequency = models.CharField(max_length=20, choices=RECURRING_FREQUENCY_CHOICES, null=True, blank=True)
    recurring_ends_on = models.DateField(null=True, blank=True)
    
    # Organizational context
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='tasks'
    )
    project = models.ForeignKey(
        'projects.Project',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tasks'
    )
    
    # Visibility settings
    visibility = models.CharField(max_length=20, choices=VISIBILITY_CHOICES, default='team')
    
    # Goals and measurements
    acceptance_criteria = models.TextField(blank=True)
    
    # Tags (comma-separated string instead of ArrayField)
    tags = models.CharField(max_length=500, blank=True)
    
    # Notes for collaborators
    notes = models.TextField(blank=True)
    
    # Time and budget tracking
    time_tracking_enabled = models.BooleanField(default=False)
    budget_hours = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    is_billable = models.BooleanField(default=False)
    client_reference = models.CharField(max_length=100, blank=True)
    
    # Task creator
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_tasks'
    )
    
    # Task assignment
    assigned_to = models.ForeignKey(
        TeamMember,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_tasks'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Approval
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_tasks'
    )
    
    # Rejection
    rejected_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='rejected_tasks'
    )
    rejection_reason = models.TextField(blank=True)
    
    # Delegation
    delegated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='delegated_tasks'
    )
    delegation_notes = models.TextField(blank=True)
    delegation_date = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return self.title
    
    def get_tags_list(self):
        """Convert comma-separated tags string to list"""
        if not self.tags:
            return []
        return [tag.strip() for tag in self.tags.split(',')]
    
    def set_tags_list(self, tags_list):
        """Convert list to comma-separated tags string"""
        if not tags_list:
            self.tags = ''
        else:
            self.tags = ', '.join(tags_list)


class TaskAssignee(models.Model):
    """Model for storing additional task assignees (many-to-many relationship)"""
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='assignees_through')
    team_member = models.ForeignKey(TeamMember, on_delete=models.CASCADE, related_name='assigned_tasks_through')
    
    class Meta:
        unique_together = ('task', 'team_member')
    
    def __str__(self):
        return f"{self.team_member.name} assigned to {self.task.title}"


class TaskApprover(models.Model):
    """Model for storing task approvers (many-to-many relationship)"""
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='approvers_through')
    team_member = models.ForeignKey(TeamMember, on_delete=models.CASCADE, related_name='approving_tasks_through')
    
    class Meta:
        unique_together = ('task', 'team_member')
    
    def __str__(self):
        return f"{self.team_member.name} approves {self.task.title}"


class TaskWatcher(models.Model):
    """Model for storing task watchers (many-to-many relationship)"""
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='watchers_through')
    team_member = models.ForeignKey(TeamMember, on_delete=models.CASCADE, related_name='watching_tasks_through')
    
    class Meta:
        unique_together = ('task', 'team_member')
    
    def __str__(self):
        return f"{self.team_member.name} watches {self.task.title}"


class TaskPrerequisite(models.Model):
    """Model for storing task prerequisites (many-to-many relationship)"""
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='prerequisites_through')
    prerequisite_task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='dependent_tasks_through')
    
    class Meta:
        unique_together = ('task', 'prerequisite_task')
    
    def __str__(self):
        return f"{self.prerequisite_task.title} is prerequisite for {self.task.title}"


class TaskLink(models.Model):
    """Model for storing linked tasks (many-to-many relationship)"""
    task1 = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='links_as_task1')
    task2 = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='links_as_task2')
    
    class Meta:
        unique_together = ('task1', 'task2')
    
    def __str__(self):
        return f"{self.task1.title} linked to {self.task2.title}"


class TaskAttachment(models.Model):
    """Model for storing task attachments"""
    
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='attachments'
    )
    file = models.FileField(upload_to='task_attachments/')
    filename = models.CharField(max_length=255)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.filename


class Comment(models.Model):
    """Model for storing task comments"""
    
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    text = models.TextField()
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Comment by {self.author} on {self.task}"


class TaskHistory(models.Model):
    """Model for tracking task changes/activity"""
    
    ACTION_CHOICES = [
        ('created', 'Created'),
        ('updated', 'Updated'),
        ('assigned', 'Assigned'),
        ('delegated', 'Delegated'),
        ('status_changed', 'Status Changed'),
        ('commented', 'Commented'),
        ('completed', 'Completed'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='history'
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    description = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.action} by {self.actor} on {self.task}"
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name_plural = "Task Histories"