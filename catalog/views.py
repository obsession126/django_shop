from django.shortcuts import get_object_or_404,redirect
from django.views.generic import TemplateView,DetailView
from django.http import HttpResponse
from django.template.response import TemplateResponse
from .models import Category,Product,Size
from django.db.models import Q
from django.core.paginator import Paginator
from django.views import View
from . forms import ReviewForm


class IndexView(TemplateView):
    template_name = 'catalog/base.html'

    def get_context_data(self,**kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        context['current_category']=None
        return context
    
    def get(self,request,*args,**kwargs):
        context = self.get_context_data(**kwargs)
        if request.headers.get('HX-Request'):
            return TemplateResponse(request,'catalog/home_context.html',context)
        return TemplateResponse(request, self.template_name, context)


class CatalogView(TemplateView):
    template_name = 'catalog/base.html'
    FILTER_MAPPING={
        'color':lambda queryset,value: queryset.filter(color__iexact=value),
        'min_price':lambda queryset,value: queryset.filter(price__gte=value),
        'max_price':lambda queryset,value: queryset.filter(price__lte=value),
        'size':lambda queryset,value: queryset.filter(product_sizes__size__name=value),     
    }


    def get_context_data(self,**kwargs):
        context = super().get_context_data(**kwargs)
        category_slug = kwargs.get('category_slug')
        categories = Category.objects.all()
        products = Product.objects.all() 
        current_category = None
        
        if category_slug:
            current_category = get_object_or_404(Category,slug=category_slug)
            products = products.filter(category=current_category)
        products = sorted(
                Product.objects.all(), 
                key=lambda p: p.popularity_score, 
                reverse=True 
                ) 

        query = self.request.GET.get('q')
        if query:
            products = products.filter(
                Q(name__icontains=query) | Q(description__icontains=query)
            )

        filter_params = {}
        for param, filter_func in self.FILTER_MAPPING.items():
            value = self.request.GET.get(param)
            if value:
                products = filter_func(products,value)
                filter_params[param] = value
            else:
                filter_params[param]=''

        filter_params['q'] = query or ''

        context.update({'categories':categories,
                        'products':products,
                        'current_category':category_slug,
                        'filter_params':filter_params,
                        'sizes':Size.objects.all(),
                        'search_query':query or ''
                        })
        if self.request.GET.get('show_search') == 'true':
            context['show_search'] = True
        elif self.request.GET.get('reset_search') == 'true':
            context['reset_search']=True

        return context
    
    def get(self,request,*args,**kwargs):
        context = self.get_context_data(**kwargs)
        if request.headers.get('HX-Request'):
            if context.get('show_search'):
                return TemplateResponse(request,'catalog/search_input.html',context)
            elif context.get('reset_search'):
                return TemplateResponse(request,'catalog/search_button.html',{})
            template = 'catalog/filter_modal.html' if request.GET.get('show_filters') == 'true' else 'catalog/catalog.html'
            return TemplateResponse(request,template,context)
        return TemplateResponse(request,self.template_name,context)
    


class ProductDetailView(DetailView):
    model = Product
    template_name = 'catalog/base.html'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'


    def get_object(self, queryset=None):
        product = super().get_object(queryset)
        product.views += 1
        product.save(update_fields=['views'])
        return product

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.get_object()
        context['categories'] = Category.objects.all()
        context['related_products'] = Product.objects.filter(
            category=product.category
        ).exclude(id=product.id)[:4]
        context['current_category'] = product.category.slug
        context['reviews'] = product.reviews.all().order_by('-created_at')
        context['form'] = ReviewForm()
        context['rating_range'] = range(1,6)
        return context
    
    def get(self,request,*args,**kwargs):
        self.object = self.get_object()
        context = self.get_context_data(**kwargs)
        if request.headers.get('HX-Request'):
            return TemplateResponse(request,'catalog/product_detail.html',context)
        return TemplateResponse(request,self.template_name,context)
    
    def post(self,request,*args,**kwargs):
        self.object = self.get_object()
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.product = self.object
            review.user = request.user
            review.save()
            return redirect('catalog:product_detail',slug=self.object.slug)
        context = self.get_context_data()
        context['form'] = form
        return TemplateResponse(request,self.template_name,context)