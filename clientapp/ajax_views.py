# clientapp/ajax_views.py
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404
from .models import Process, ProcessTier, ProcessVariable, ProcessVariableRange, ProductImage
import json
from decimal import Decimal


def ajax_process_tiers(request, process_id):
    """Get tier pricing for a process"""
    try:
        process = get_object_or_404(Process, pk=process_id)

        if process.pricing_type != 'tier':
            return JsonResponse({
                'success': False,
                'error': 'Process is not tier-based'
            })

        tiers = ProcessTier.objects.filter(process=process).order_by('tier_number')
        tier_data = []

        for tier in tiers:
            tier_data.append({
                'tier_number': tier.tier_number,
                'quantity_from': tier.quantity_from,
                'quantity_to': tier.quantity_to,
                'cost': float(tier.cost),
                'price': float(tier.price)
            })

        return JsonResponse({
            'success': True,
            'process_name': process.process_name,
            'tiers': tier_data
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


def ajax_process_variables(request, process_id):
    """Get variables for a formula-based process"""
    try:
        process = get_object_or_404(Process, pk=process_id)

        if process.pricing_type != 'formula':
            return JsonResponse({
                'success': False,
                'error': 'Process is not formula-based'
            })

        variables = ProcessVariable.objects.filter(process=process).order_by('order')
        variable_data = []

        for variable in variables:
            # Get ranges for this variable
            ranges = ProcessVariableRange.objects.filter(variable=variable).order_by('min_value')
            range_data = []

            for range_obj in ranges:
                range_data.append({
                    'min_value': float(range_obj.min_value),
                    'max_value': float(range_obj.max_value),
                    'price': float(range_obj.price),
                    'rate': float(range_obj.rate)
                })

            variable_data.append({
                'id': variable.pk,
                'name': variable.variable_name,
                'type': variable.variable_type,
                'unit': variable.unit,
                'min_value': float(variable.min_value) if variable.min_value else None,
                'max_value': float(variable.max_value) if variable.max_value else None,
                'default_value': float(variable.default_value) if variable.default_value else None,
                'description': variable.description,
                'ranges': range_data
            })

        return JsonResponse({
            'success': True,
            'process_name': process.process_name,
            'variables': variable_data
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@csrf_exempt
@require_POST
def ajax_calculate_pricing(request, process_id):
    """Calculate pricing for a formula-based process"""
    try:
        process = get_object_or_404(Process, pk=process_id)

        if process.pricing_type != 'formula':
            return JsonResponse({
                'success': False,
                'error': 'Process is not formula-based'
            })

        # Parse variables from request
        data = json.loads(request.body)
        variables = data.get('variables', {})
        quantity = data.get('quantity', 1)

        print(f"DEBUG: ajax_calculate_pricing called for process {process_id}")
        print(f"DEBUG: Received variables: {variables}")
        print(f"DEBUG: Quantity: {quantity}")

        total_cost = Decimal('0')
        breakdown = []

        # Calculate for each variable
        for var_name, var_value in variables.items():
            try:
                var_value = Decimal(str(var_value))
            except:
                continue

            print(f"DEBUG: Processing variable '{var_name}' with value {var_value}")

            # Find the variable
            try:
                variable = ProcessVariable.objects.get(
                    process=process,
                    variable_name=var_name
                )
                print(f"DEBUG: Found variable: {variable.variable_name} (ID: {variable.pk})")
            except ProcessVariable.DoesNotExist:
                print(f"DEBUG: Variable '{var_name}' not found in process {process_id}")
                continue

            # Find applicable range
            applicable_range = ProcessVariableRange.objects.filter(
                variable=variable,
                min_value__lte=var_value,
                max_value__gte=var_value
            ).first()

            if applicable_range:
                # Calculate cost: (price * rate) * quantity
                cost = (applicable_range.price * applicable_range.rate) * quantity
                total_cost += cost

                breakdown.append({
                    'component': f'{var_name} Cost',
                    'calculation': f'{applicable_range.price} × {applicable_range.rate} × {quantity}',
                    'amount': float(cost)
                })
                print(f"DEBUG: Added cost for {var_name}: {cost}")
            else:
                print(f"DEBUG: No applicable range found for {var_name} = {var_value}")

        print(f"DEBUG: Final breakdown: {breakdown}")
        print(f"DEBUG: Total cost: {total_cost}")

        return JsonResponse({
            'success': True,
            'total_cost': float(total_cost),
            'breakdown': breakdown
        })

    except Exception as e:
        print(f"DEBUG: Error in ajax_calculate_pricing: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


# Image management endpoints (placeholders - implement as needed)
def ajax_get_product_image(request, image_id):
    """Get product image metadata"""
    try:
        image = get_object_or_404(ProductImage, pk=image_id)
        return JsonResponse({
            'success': True,
            'image_url': image.image.url,
            'alt_text': image.alt_text,
            'caption': image.caption,
            'image_type': image.image_type,
            'file_name': image.image.name.split('/')[-1],
            'file_size': image.image.size,
            'dimensions': f"{image.image.width}x{image.image.height}" if image.image.width else None
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@csrf_exempt
@require_POST
def ajax_update_product_image(request, image_id):
    """Update product image metadata"""
    try:
        image = get_object_or_404(ProductImage, pk=image_id)
        data = json.loads(request.body)

        image.alt_text = data.get('alt_text', image.alt_text)
        image.caption = data.get('caption', image.caption)
        image.image_type = data.get('image_type', image.image_type)
        image.save()

        return JsonResponse({
            'success': True,
            'message': 'Image updated successfully'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@csrf_exempt
@require_POST
def ajax_delete_product_image(request, image_id):
    """Delete product image"""
    try:
        image = get_object_or_404(ProductImage, pk=image_id)
        image.delete()

        return JsonResponse({
            'success': True,
            'message': 'Image deleted successfully'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@csrf_exempt
@require_POST
def ajax_replace_product_image(request, image_id):
    """Replace product image file"""
    try:
        image = get_object_or_404(ProductImage, pk=image_id)

        if 'image' in request.FILES:
            image.image = request.FILES['image']
            image.save()

            return JsonResponse({
                'success': True,
                'message': 'Image replaced successfully',
                'new_image_url': image.image.url
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'No image file provided'
            })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })