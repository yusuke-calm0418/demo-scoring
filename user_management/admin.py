from django.contrib import admin
from .models import CustomUser, Company
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _

class CustomUserAdmin(UserAdmin):
    list_display = ('name', 'email', 'is_staff',)
    ordering = ('-date_joined',)
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('company_name', 'name', 'kana_name', 'phone_number', 'postal_code', 'address', 'industry')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login',)}),
    )
    readonly_fields = ('date_joined',)  # 追加

admin.site.register(CustomUser, CustomUserAdmin)

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'address', 'industry', 'created_at')
    search_fields = ('name', 'industry')
