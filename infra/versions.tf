terraform {
  required_version = ">= 1.9"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 5.14"
    }
  }

  # Estado local por ahora (gratis). Para compartir el estado entre el equipo
  # se puede migrar a un backend "azurerm" en un Storage Account (tiene costo
  # mínimo; se consultará antes de activarlo).
}

provider "azurerm" {
  features {}
  subscription_id = var.subscription_id
}
