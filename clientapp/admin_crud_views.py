from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse, HttpResponseForbidden
from django.db.models import Q, Count
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.urls import reverse
from django.forms.models import model_to_dict
from django.utils.html import escape
import json


class AdminListView:
    """Base class for Django admin-style list views"""
    
    model = None
    template_name = 'admin/generic_list.html'
    paginate_by = 25
    search_fields = []
    filter_fields = []
    list_display = []
    
    def get_queryset(self):
        """Get the queryset, filtering by search and status if applicable"""
        queryset = self.model.objects.all()
        
        search = self.request.GET.get('q', '')
        if search and self.search_fields:
            search_query = Q()
            for field in self.search_fields:
                search_query |= Q(**{f"{field}__icontains": search})
            queryset = queryset.filter(search_query)
        
        # Filter by any filter fields
        for field in self.filter_fields:
            value = self.request.GET.get(field, '')
            if value:
                queryset = queryset.filter(**{field: value})
        
        return queryset.order_by('-created_at', '-id')
    
    def get_context_data(self, **kwargs):
        """Build context for template"""
        queryset = self.get_queryset()
        paginator = Paginator(queryset, self.paginate_by)
        
        try:
            page = paginator.page(self.request.GET.get('page', 1))
        except (EmptyPage, PageNotAnInteger):
            page = paginator.page(1)
        
        context = {
            'title': self.model._meta.verbose_name_plural,
            'page_obj': page,
            'object_list': page.object_list,
            'search': self.request.GET.get('q', ''),
            'total_count': queryset.count(),
            'model_name': self.model._meta.model_name,
        }
        
        # Add filter values to context
        for field in self.filter_fields:
            context[field] = self.request.GET.get(field, '')
        
        return context
    
    def render_to_response(self, context):
        """Render the template"""
        return render(self.request, self.template_name, context)
    
    def get(self, request, *args, **kwargs):
        """Handle GET request"""
        self.request = request
        context = self.get_context_data()
        return self.render_to_response(context)


class AdminDetailView:
    """Base class for Django admin-style detail/edit views"""
    
    model = None
    form_class = None
    template_name = 'admin/detail_view.html'
    
    def get_object(self):
        """Get the object to display"""
        pk = self.kwargs.get('pk')
        return get_object_or_404(self.model, pk=pk)
    
    def get_form_class(self):
        """Get the form class"""
        if self.form_class:
            return self.form_class
        # Generate a basic ModelForm
        from django import forms
        
        class BasicModelForm(forms.ModelForm):
            class Meta:
                model = self.model
                fields = '__all__'
        
        return BasicModelForm
    
    def get_context_data(self, **kwargs):
        """Build context for template"""
        obj = self.get_object()
        form_class = self.get_form_class()
        form = form_class(instance=obj)
        
        context = {
            'object': obj,
            'form': form,
            'model_name': self.model._meta.model_name,
            'title': f"Edit {self.model._meta.verbose_name}",
        }
        
        return context
    
    def render_to_response(self, context):
        """Render the template"""
        return render(self.request, self.template_name, context)
    
    def get(self, request, *args, **kwargs):
        """Handle GET request"""
        self.request = request
        self.kwargs = kwargs
        context = self.get_context_data()
        return self.render_to_response(context)
    
    def post(self, request, *args, **kwargs):
        """Handle POST request (form submission)"""
        self.request = request
        self.kwargs = kwargs
        obj = self.get_object()
        form_class = self.get_form_class()
        form = form_class(request.POST, instance=obj)
        
        if form.is_valid():
            form.save()
            messages.success(request, f"{obj.__class__.__name__} updated successfully")
            return redirect('admin:' + self.model._meta.model_name + '_change', pk=obj.pk)
        
        context = {
            'object': obj,
            'form': form,
            'model_name': self.model._meta.model_name,
            'title': f"Edit {self.model._meta.verbose_name}",
        }
        
        return self.render_to_response(context)


class AdminAddView:
    """Base class for Django admin-style add views"""
    
    model = None
    form_class = None
    template_name = 'admin/detail_view.html'
    
    def get_form_class(self):
        """Get the form class"""
        if self.form_class:
            return self.form_class
        # Generate a basic ModelForm
        from django import forms
        
        class BasicModelForm(forms.ModelForm):
            class Meta:
                model = self.model
                fields = '__all__'
        
        return BasicModelForm
    
    def get_context_data(self, **kwargs):
        """Build context for template"""
        form_class = self.get_form_class()
        form = form_class()
        
        context = {
            'form': form,
            'model_name': self.model._meta.model_name,
            'title': f"Add {self.model._meta.verbose_name}",
            'is_add': True,
        }
        
        return context
    
    def render_to_response(self, context):
        """Render the template"""
        return render(self.request, self.template_name, context)
    
    def get(self, request, *args, **kwargs):
        """Handle GET request"""
        self.request = request
        context = self.get_context_data()
        return self.render_to_response(context)
    
    def post(self, request, *args, **kwargs):
        """Handle POST request (form submission)"""
        self.request = request
        form_class = self.get_form_class()
        form = form_class(request.POST)
        
        if form.is_valid():
            obj = form.save()
            messages.success(request, f"{obj.__class__.__name__} created successfully")
            return redirect('admin:' + self.model._meta.model_name + '_change', pk=obj.pk)
        
        context = {
            'form': form,
            'model_name': self.model._meta.model_name,
            'title': f"Add {self.model._meta.verbose_name}",
            'is_add': True,
        }
        
        return self.render_to_response(context)


class AdminDeleteView:
    """Base class for Django admin-style delete views"""
    
    model = None
    template_name = 'admin/delete_confirm.html'
    
    def get_object(self):
        """Get the object to delete"""
        pk = self.kwargs.get('pk')
        return get_object_or_404(self.model, pk=pk)
    
    def get_context_data(self, **kwargs):
        """Build context for template"""
        obj = self.get_object()
        
        context = {
            'object': obj,
            'model_name': self.model._meta.model_name,
            'title': f"Delete {self.model._meta.verbose_name}",
        }
        
        return context
    
    def render_to_response(self, context):
        """Render the template"""
        return render(self.request, self.template_name, context)
    
    def get(self, request, *args, **kwargs):
        """Handle GET request (confirmation page)"""
        self.request = request
        self.kwargs = kwargs
        context = self.get_context_data()
        return self.render_to_response(context)
    
    def post(self, request, *args, **kwargs):
        """Handle POST request (actual deletion)"""
        self.request = request
        self.kwargs = kwargs
        obj = self.get_object()
        obj_display = str(obj)
        obj.delete()
        messages.success(request, f"{obj_display} deleted successfully")
        return redirect('admin:' + self.model._meta.model_name + '_changelist')


# Decorator-based function views for list views
@staff_member_required
def create_list_view(model, search_fields=None, filter_fields=None, paginate_by=25):
    """Factory function to create a list view for a model"""
    
    def list_view(request):
        search_fields_list = search_fields or []
        filter_fields_list = filter_fields or []
        
        queryset = model.objects.all()
        
        # Search
        search = request.GET.get('q', '')
        if search and search_fields_list:
            search_query = Q()
            for field in search_fields_list:
                search_query |= Q(**{f"{field}__icontains": search})
            queryset = queryset.filter(search_query)
        
        # Filter
        for field in filter_fields_list:
            value = request.GET.get(field, '')
            if value:
                queryset = queryset.filter(**{field: value})
        
        # Order by
        queryset = queryset.order_by('-created_at', '-id')
        
        # Paginate
        paginator = Paginator(queryset, paginate_by)
        try:
            page = paginator.page(request.GET.get('page', 1))
        except (EmptyPage, PageNotAnInteger):
            page = paginator.page(1)
        
        context = {
            'title': model._meta.verbose_name_plural,
            'page_obj': page,
            'object_list': page.object_list,
            'search': search,
            'total_count': queryset.count(),
            'model_name': model._meta.model_name,
        }
        
        # Add filter values
        for field in filter_fields_list:
            context[field] = request.GET.get(field, '')
        
        return render(request, 'admin/generic_list.html', context)
    
    return list_view


@staff_member_required
@require_http_methods(["GET", "POST"])
def create_detail_view(model, form_class=None):
    """Factory function to create a detail/edit view for a model"""
    
    def detail_view(request, pk):
        obj = get_object_or_404(model, pk=pk)
        
        if form_class:
            form_class_to_use = form_class
        else:
            from django import forms
            model_ref = model
            class BasicModelForm(forms.ModelForm):
                class Meta:
                    model = model_ref
                    fields = '__all__'
            form_class_to_use = BasicModelForm
        
        if request.method == 'POST':
            form = form_class_to_use(request.POST, instance=obj)
            if form.is_valid():
                form.save()
                messages.success(request, f"{obj.__class__.__name__} updated successfully")
                return redirect('admin:' + model._meta.model_name + '_change', pk=obj.pk)
        else:
            form = form_class_to_use(instance=obj)
        
        context = {
            'object': obj,
            'form': form,
            'model_name': model._meta.model_name,
            'title': f"Edit {obj.__class__.__name__}",
        }
        
        return render(request, 'admin/detail_view.html', context)
    
    return detail_view


@staff_member_required
@require_http_methods(["GET", "POST"])
def create_add_view(model, form_class=None):
    """Factory function to create an add view for a model"""
    
    def add_view(request):
        if form_class:
            form_class_to_use = form_class
        else:
            from django import forms
            model_ref = model
            class BasicModelForm(forms.ModelForm):
                class Meta:
                    model = model_ref
                    fields = '__all__'
            form_class_to_use = BasicModelForm
        
        if request.method == 'POST':
            form = form_class_to_use(request.POST)
            if form.is_valid():
                obj = form.save()
                messages.success(request, f"{obj.__class__.__name__} created successfully")
                return redirect('admin:' + model._meta.model_name + '_change', pk=obj.pk)
        else:
            form = form_class_to_use()
        
        context = {
            'form': form,
            'model_name': model._meta.model_name,
            'title': f"Add {model._meta.verbose_name}",
            'is_add': True,
        }
        
        return render(request, 'admin/detail_view.html', context)
    
    return add_view


@staff_member_required
@require_http_methods(["GET", "POST"])
def create_delete_view(model):
    """Factory function to create a delete view for a model"""
    
    def delete_view(request, pk):
        obj = get_object_or_404(model, pk=pk)
        
        if request.method == 'POST':
            obj_display = str(obj)
            obj.delete()
            messages.success(request, f"{obj_display} deleted successfully")
            return redirect('admin:' + model._meta.model_name + '_changelist')
        
        context = {
            'object': obj,
            'model_name': model._meta.model_name,
            'title': f"Delete {obj.__class__.__name__}",
        }
        
        return render(request, 'admin/delete_confirm.html', context)
    
    return delete_view
