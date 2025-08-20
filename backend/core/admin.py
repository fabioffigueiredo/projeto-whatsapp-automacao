from django.contrib import admin
from .models import (ProviderConfig, MessageTemplate, Conversation, MessageLog,
                     WebhookLog, Client, Operation)

@admin.register(ProviderConfig)
class ProviderConfigAdmin(admin.ModelAdmin):
    list_display = ("type","name","active")
    list_filter = ("type","active")
    search_fields = ("name",)

@admin.register(MessageTemplate)
class MessageTemplateAdmin(admin.ModelAdmin):
    list_display = ("code","locale")
    search_fields = ("code","text")

@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ("external_user_id","state_node","is_active","last_seen")
    list_filter = ("is_active","state_node")
    search_fields = ("external_user_id",)

@admin.register(MessageLog)
class MessageLogAdmin(admin.ModelAdmin):
    list_display = ("conversation","direction","status","created_at")
    list_filter = ("direction","status")
    search_fields = ("payload",)
    date_hierarchy = "created_at"

@admin.register(WebhookLog)
class WebhookLogAdmin(admin.ModelAdmin):
    list_display = ("source","status","received_at")
    list_filter = ("source","status")
    date_hierarchy = "received_at"

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ("name","phone","email","external_id")
    search_fields = ("name","phone","email","external_id")

@admin.register(Operation)
class OperationAdmin(admin.ModelAdmin):
    list_display = ("id","client","amount_usd","rate_used","amount_brl_estimated","status","updated_at")
    list_filter = ("status",)
    search_fields = ("client__name","payment_provider_ref")
    date_hierarchy = "updated_at"

