"""
Product Configuration Rules Engine
Validates product variable combinations
"""
from typing import Dict, Any, List
from django.core.exceptions import ValidationError

from ..models import Product, ProductRule


class ProductConfigurationValidator:
    """
    Product Configuration Rules Engine
    Validates product variable combinations
    """
    
    @staticmethod
    def validate(
        product_id: int,
        variables: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate product configuration
        
        Args:
            product_id: Product ID
            variables: Product variables dict (e.g., {"paper": "300gsm", "finish": "spot_uv"})
        
        Returns:
            {
                "valid": bool,
                "errors": [str],
                "warnings": [str]
            }
        """
        try:
            product = Product.objects.get(pk=product_id)
        except Product.DoesNotExist:
            return {
                "valid": False,
                "errors": ["Product not found"],
                "warnings": []
            }
        
        errors = []
        warnings = []
        
        # Get all active rules for this product
        rules = ProductRule.objects.filter(
            product=product,
            is_active=True
        ).order_by('-priority')
        
        for rule in rules:
            validation_result = ProductConfigurationValidator._validate_rule(
                rule, variables
            )
            
            if validation_result["valid"] is False:
                errors.append(validation_result["message"])
            elif validation_result.get("warning"):
                warnings.append(validation_result["message"])
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    @staticmethod
    def _validate_rule(rule: ProductRule, variables: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a single rule"""
        condition = rule.condition_json
        
        if rule.rule_type == 'requires':
            return ProductConfigurationValidator._validate_requires(rule, condition, variables)
        elif rule.rule_type == 'excludes':
            return ProductConfigurationValidator._validate_excludes(rule, condition, variables)
        elif rule.rule_type == 'range':
            return ProductConfigurationValidator._validate_range(rule, condition, variables)
        elif rule.rule_type == 'conditional':
            return ProductConfigurationValidator._validate_conditional(rule, condition, variables)
        elif rule.rule_type == 'turnaround_compatibility':
            return ProductConfigurationValidator._validate_turnaround(rule, condition, variables)
        
        return {"valid": True, "message": None}
    
    @staticmethod
    def _validate_requires(rule: ProductRule, condition: Dict, variables: Dict[str, Any]) -> Dict[str, Any]:
        """Validate 'requires' rule"""
        required_var = condition.get('variable')
        required_value = condition.get('value')
        
        if required_var in variables:
            if variables[required_var] == required_value:
                # Check if required dependent variable is present
                dependent_var = condition.get('requires_variable')
                if dependent_var and dependent_var not in variables:
                    return {
                        "valid": False,
                        "message": rule.message or f"{dependent_var} is required when {required_var} is {required_value}"
                    }
        
        return {"valid": True}
    
    @staticmethod
    def _validate_excludes(rule: ProductRule, condition: Dict, variables: Dict[str, Any]) -> Dict[str, Any]:
        """Validate 'excludes' rule"""
        var_name = condition.get('variable')
        excluded_values = condition.get('excludes', [])
        
        if var_name in variables:
            if variables[var_name] in excluded_values:
                return {
                    "valid": False,
                    "message": rule.message
                }
        
        return {"valid": True}
    
    @staticmethod
    def _validate_range(rule: ProductRule, condition: Dict, variables: Dict[str, Any]) -> Dict[str, Any]:
        """Validate 'range' rule (min/max quantity, etc.)"""
        var_name = condition.get('variable')
        min_value = condition.get('min')
        max_value = condition.get('max')
        
        if var_name in variables:
            value = variables[var_name]
            try:
                value = float(value)
                if min_value is not None and value < min_value:
                    return {
                        "valid": False,
                        "message": rule.message or f"{var_name} must be at least {min_value}"
                    }
                if max_value is not None and value > max_value:
                    return {
                        "valid": False,
                        "message": rule.message or f"{var_name} must be at most {max_value}"
                    }
            except (ValueError, TypeError):
                pass
        
        return {"valid": True}
    
    @staticmethod
    def _validate_conditional(rule: ProductRule, condition: Dict, variables: Dict[str, Any]) -> Dict[str, Any]:
        """Validate 'conditional' rule"""
        # Complex conditional logic
        if_condition = condition.get('if')
        then_condition = condition.get('then')
        
        if if_condition:
            if_var = if_condition.get('variable')
            if_value = if_condition.get('value')
            
            if if_var in variables and variables[if_var] == if_value:
                # Then condition must be met
                then_var = then_condition.get('variable')
                then_value = then_condition.get('value')
                
                if then_var not in variables or variables[then_var] != then_value:
                    return {
                        "valid": False,
                        "message": rule.message
                    }
        
        return {"valid": True}
    
    @staticmethod
    def _validate_turnaround(rule: ProductRule, condition: Dict, variables: Dict[str, Any]) -> Dict[str, Any]:
        """Validate turnaround compatibility"""
        # Check if selected variables are compatible with turnaround time
        turnaround_id = variables.get('turnaround_id')
        if turnaround_id:
            incompatible_vars = condition.get('incompatible_variables', {})
            for var_name, var_value in variables.items():
                if var_name in incompatible_vars:
                    if var_value in incompatible_vars[var_name]:
                        return {
                            "valid": False,
                            "message": rule.message
                        }
        
        return {"valid": True}

