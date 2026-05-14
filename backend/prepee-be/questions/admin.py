from django.contrib import admin
from .models import Questions

@admin.register(Questions)
class QuestionsAdmin(admin.ModelAdmin):
    list_display = ('id', 'subject', 'text', 'correct_option')
    list_filter = ('subject', 'correct_option')
    search_fields = ('subject', 'text')
    fieldsets = (
        (None, {
            'fields': ('subject', 'text', 'explanation')
        }),
        ('Options', {
            'fields': (('option_a', 'option_b', 'option_c', 'option_d'), 'correct_option')
        }),
    )