output "resource_group_name" {
  value = azurerm_resource_group.main.name
}

output "static_web_app_url" {
  description = "URL pública de la plataforma"
  value       = "https://${azurerm_static_web_app.web.default_host_name}"
}

output "static_web_app_deployment_token" {
  description = "Token para GitHub Actions (secret AZURE_STATIC_WEB_APPS_API_TOKEN). Ver: terraform output -raw static_web_app_deployment_token"
  value       = azurerm_static_web_app.web.api_key
  sensitive   = true
}
