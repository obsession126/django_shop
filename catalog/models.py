from django.db import models
from django.utils.text import slugify
from django.utils import timezone
import math
from users.models import CustomUser
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from django.db.models import Avg



analyzer = SentimentIntensityAnalyzer()
def analyze_review_text(text):
     result = analyzer.polarity_scores(text)
     return result['compound']


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True,max_length=100)


    def save(self,*args,**kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args,**kwargs)

    
    def __str__(self):
        return self.name
    



class Size(models.Model):
    name = models.CharField(max_length=20)


    def __str__(self):
        return self.name
    


class ProductSize(models.Model):
    product = models.ForeignKey('Product',on_delete=models.CASCADE,related_name='product_sizes')
    size = models.ForeignKey(Size,on_delete=models.CASCADE)
    stock = models.PositiveBigIntegerField(default=0)

    def __str__(self):
        return f"{self.size.name} ({self.stock} in stock) for {self.product.name}"






class Product(models.Model):
    name = models.CharField(max_length=100)
    slug = models.CharField(max_length=100,unique=True)
    category = models.ForeignKey(Category,on_delete=models.CASCADE, related_name='products')
    color = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10,decimal_places=2)
    description = models.TextField(blank=True)
    main_image = models.ImageField(upload_to='products/main/')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    views = models.PositiveIntegerField(default=0)
    cart_adds = models.PositiveIntegerField(default=0)
    

    @property
    def popularity_score(self):
        reviews = self.reviews.all()
        if not reviews.exists():
            return 0
        
        avg_user_rating = reviews.aggregate(Avg('rating'))['rating__avg']
        avg_sentiment = reviews.aggregate(Avg('sentiment_score'))['sentiment_score__avg']
        days_passed = (timezone.now() - self.updated_at).days
        decay_factor = math.exp(-days_passed / 7)
        avg_sentiment=(avg_sentiment+1)/2
        return (math.log(self.views+1) + self.cart_adds*(avg_user_rating*0.3+avg_sentiment*0.6)) * decay_factor



    def save(self,*args,**kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args,**kwargs)


    def __str__(self):
        return self.name



class ProductImage(models.Model):
    product =  models.ForeignKey(Product,on_delete=models.CASCADE,related_name='images')

    image = models.ImageField(upload_to="products/extra/")



class Review(models.Model):
    product = models.ForeignKey('Product', on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey('users.CustomUser', on_delete=models.CASCADE,related_name='reviews') 
    rating = models.PositiveSmallIntegerField(default=3)
    text = models.TextField()
    sentiment_score = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)

  

    def save(self, *args, **kwargs):
        self.sentiment_score = analyze_review_text(self.text)
        super().save(*args, **kwargs)



    def __str__(self):
        return f"{self.user} → {self.product.name} ({self.rating})"
    