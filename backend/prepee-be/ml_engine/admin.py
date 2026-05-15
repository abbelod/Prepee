from django.contrib import admin
from .models import Question, QuestionAttempt, StudentProfile, CheatingFlag


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('id', 'subject', 'topic', 'bloom_level', 'difficulty_score', 'text_short')
    list_filter = ('subject', 'bloom_level', 'topic')
    search_fields = ('text', 'topic')
    ordering = ('subject', 'topic', 'difficulty_score')

    def text_short(self, obj):
        return obj.text[:80] + '...' if len(obj.text) > 80 else obj.text
    text_short.short_description = 'Question'


@admin.register(QuestionAttempt)
class QuestionAttemptAdmin(admin.ModelAdmin):
    list_display = ('id', 'student', 'question_id', 'is_correct', 'time_taken_seconds', 'created_at')
    list_filter = ('is_correct', 'created_at')
    search_fields = ('student__username', 'student__email')
    raw_id_fields = ('student', 'question', 'match')


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'accuracy_rate', 'total_questions_attempted', 'avg_time_per_question', 'updated_at')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('updated_at',)


@admin.register(CheatingFlag)
class CheatingFlagAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'match_id', 'flag_type', 'severity', 'reviewed', 'created_at')
    list_filter = ('flag_type', 'severity', 'reviewed')
    search_fields = ('user__username', 'user__email')
    actions = ['mark_reviewed']

    def mark_reviewed(self, request, queryset):
        queryset.update(reviewed=True)
    mark_reviewed.short_description = "Mark selected flags as reviewed"
