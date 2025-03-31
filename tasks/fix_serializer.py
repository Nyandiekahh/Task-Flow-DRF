# tasks/fix_serializer.py

def fix_taskserializers():
    with open('tasks/serializers.py', 'r') as file:
        content = file.read()
    
    # Replace getlist with get
    content = content.replace(
        "assignees_data = self.initial_data.getlist('assignees[]', [])",
        "assignees_data = self.initial_data.get('assignees[]', [])"
    )
    content = content.replace(
        "approvers_data = self.initial_data.getlist('approvers[]', [])",
        "approvers_data = self.initial_data.get('approvers[]', [])"
    )
    content = content.replace(
        "watchers_data = self.initial_data.getlist('watchers[]', [])",
        "watchers_data = self.initial_data.get('watchers[]', [])"
    )
    content = content.replace(
        "prerequisites_data = self.initial_data.getlist('prerequisites[]', [])",
        "prerequisites_data = self.initial_data.get('prerequisites[]', [])"
    )
    content = content.replace(
        "linked_tasks_data = self.initial_data.getlist('linked_tasks[]', [])",
        "linked_tasks_data = self.initial_data.get('linked_tasks[]', [])"
    )
    
    # Fix the second instance of getlist in the update method as well
    content = content.replace(
        "assignees_data = self.initial_data.getlist('assignees[]', None)",
        "assignees_data = self.initial_data.get('assignees[]', None)"
    )
    content = content.replace(
        "approvers_data = self.initial_data.getlist('approvers[]', None)",
        "approvers_data = self.initial_data.get('approvers[]', None)"
    )
    content = content.replace(
        "watchers_data = self.initial_data.getlist('watchers[]', None)",
        "watchers_data = self.initial_data.get('watchers[]', None)"
    )
    content = content.replace(
        "prerequisites_data = self.initial_data.getlist('prerequisites[]', None)",
        "prerequisites_data = self.initial_data.get('prerequisites[]', None)"
    )
    content = content.replace(
        "linked_tasks_data = self.initial_data.getlist('linked_tasks[]', None)",
        "linked_tasks_data = self.initial_data.get('linked_tasks[]', None)"
    )
    
    # Add a conversion from string to list for tags
    content = content.replace(
        "if 'tags[]' in self.initial_data:",
        "if 'custom_tags' in self.initial_data:"
    )
    
    with open('tasks/serializers.py', 'w') as file:
        file.write(content)

if __name__ == "__main__":
    fix_taskserializers()
    print("Serializers fixed successfully.")