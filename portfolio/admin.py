from django.contrib import admin
from .models import InvestigationCase, CaseWallet


class CaseWalletInline(admin.TabularInline):
    model = CaseWallet
    extra = 0
    readonly_fields = ('added_at',)
    autocomplete_fields = ['wallet']


@admin.register(InvestigationCase)
class InvestigationCaseAdmin(admin.ModelAdmin):
    list_display = ('name', 'investigator', 'status', 'priority', 'wallet_count', 'created_at')
    list_filter = ('status', 'priority', 'created_at')
    search_fields = ('name', 'description', 'notes')
    readonly_fields = ('created_at', 'updated_at', 'wallet_count', 'transaction_count')
    inlines = [CaseWalletInline]
    
    fieldsets = (
        ('Case Information', {
            'fields': ('name', 'description', 'investigator', 'status', 'priority')
        }),
        ('Investigation Details', {
            'fields': ('notes',)
        }),
        ('Statistics', {
            'fields': ('wallet_count', 'transaction_count', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        if not request.user.is_superuser:
            queryset = queryset.filter(investigator=request.user)
        return queryset